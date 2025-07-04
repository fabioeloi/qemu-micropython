#include "py/runtime.h"
#include "py/stream.h"
#include "py/mperrno.h"
#include "py/objstr.h"
#include <string.h> // For strlen, memcpy

// Semihosting operation numbers
#define SYS_OPEN   0x01
#define SYS_CLOSE  0x02
#define SYS_WRITEC 0x03 // Write a character (alternative to SYS_WRITE0 for single chars)
#define SYS_WRITE0 0x04 // Write a null-terminated string
#define SYS_WRITE  0x05 // Write a block of data
#define SYS_READ   0x06
#define SYS_READC  0x07 // Read a character
#define SYS_ISERROR 0x08
#define SYS_ISTTY  0x09
#define SYS_SEEK   0x0A
#define SYS_FLEN   0x0C
#define SYS_TMPNAM 0x0D // Not implemented here
#define SYS_REMOVE 0x0E
#define SYS_RENAME 0x0F
#define SYS_CLOCK  0x10
#define SYS_TIME   0x11
#define SYS_SYSTEM 0x12 // Execute a host command (security risk, not implemented)
#define SYS_ERRNO  0x13
#define SYS_GET_CMDLINE 0x15 // Get command line (can be used for is_semihosting_available)
#define SYS_HEAPINFO 0x16    // Not standard in all specs, used by some for heap info
#define SYS_ELAPSED 0x30     // Not standard in all specs
#define SYS_TICKFREQ 0x31    // Not standard in all specs

// ADP_Stopped_ApplicationExit for SYS_REPORTEXCEPTION (0x18)
#define ADP_STOPPED_APPLICATIONEXIT 0x20026 // Standard reason code for graceful exit
#define SYS_REPORTEXCEPTION 0x18            // Standard semihosting op for signalling exceptions/exit

// Semihosting open modes (map to common POSIX-like integer modes)
// Mode bits: 0: r, 1: w, 2: a, 3: r+, 4: w+, 5: a+
// Binary bit: add 'b' for binary, e.g., "rb" mode 0. Text mode is often default.
// Semihosting modes: 0:r, 1:rb, 2:r+, 3:r+b, 4:w, 5:wb, 6:w+, 7:w+b, 8:a, 9:ab, 10:a+, 11:a+b
#define SEMIHOSTING_OPEN_R   0  // r (read, text)
#define SEMIHOSTING_OPEN_RB  1  // rb (read, binary)
#define SEMIHOSTING_OPEN_RP  2  // r+ (read/write, text)
#define SEMIHOSTING_OPEN_RBP 3  // r+b (read/write, binary)
#define SEMIHOSTING_OPEN_W   4  // w (write, text)
#define SEMIHOSTING_OPEN_WB  5  // wb (write, binary)
#define SEMIHOSTING_OPEN_WP  6  // w+ (read/write truncate, text)
#define SEMIHOSTING_OPEN_WBP 7  // w+b (read/write truncate, binary)
#define SEMIHOSTING_OPEN_A   8  // a (append, text)
#define SEMIHOSTING_OPEN_AB  9  // ab (append, binary)
#define SEMIHOSTING_OPEN_AP  10 // a+ (read/append, text)
#define SEMIHOSTING_OPEN_ABP 11 // a+b (read/append, binary)


// Forward declaration for file type
extern const mp_obj_type_t mp_type_semihosting_file;

// Core semihosting call function
static inline mp_int_t do_semihosting_call(mp_int_t operation, void *params) {
    mp_int_t result;
    __asm__ volatile (
        "mov r0, %[op] \n"    // Operation number in R0
        "mov r1, %[arg] \n"   // Argument block pointer in R1
        #if defined(__thumb__) && !defined(__thumb2__) // Thumb-1 (e.g. ARMv6-M, ARMv7-M without Thumb-2)
        ".balign 4 \n"        // Ensure alignment for following instruction if needed
        "bkpt 0xAB \n"        // Breakpoint instruction for semihosting in Thumb-1
                              // Some old docs might say `svc 0xAB`, but `bkpt 0xAB` is common for Thumb
        #else // ARM or Thumb-2 (e.g. ARMv7-A, ARMv7-M with Thumb-2)
        "svc 0x123456 \n"     // Standard ARM semihosting SVC
        #endif
        "mov %[res], r0 \n"   // Result from R0
        : [res] "=r" (result) // Output
        : [op] "r" (operation), [arg] "r" (params) // Input
        : "r0", "r1", "memory", "cc" // Clobbers
    );
    return result;
}

static mp_int_t get_host_errno() {
    return do_semihosting_call(SYS_ERRNO, NULL);
}

// Helper to convert host errno to MicroPython errno
static int mp_get_errno_from_host(int host_errno) {
    // This is a very basic mapping. A more comprehensive one would be needed for full POSIX compliance.
    // Common errnos (may vary by host OS where semihosting is implemented):
    // From newlib (common C library for embedded):
    // EPERM 1, ENOENT 2, ESRCH 3, EINTR 4, EIO 5, ENXIO 6, E2BIG 7, ENOEXEC 8, EBADF 9, ...
    // For now, a direct passthrough or a few common ones.
    switch (host_errno) {
        case 0: return 0; // Success (though not an errno)
        case 1: return MP_EPERM;
        case 2: return MP_ENOENT;
        case 4: return MP_EINTR;
        case 5: return MP_EIO;
        case 9: return MP_EBADF;
        case 12: return MP_ENOMEM; // Typically ENOMEM is 12
        case 13: return MP_EACCES;
        case 17: return MP_EEXIST;
        case 22: return MP_EINVAL;
        // Add more as identified
        default: return host_errno; // Fallback to host_errno if unknown
    }
}


// --- SemihostingFile Type ---
typedef struct _mp_obj_semihosting_file_t {
    mp_obj_base_t base;
    mp_int_t host_fd; // Host file descriptor
    mp_uint_t current_pos; // Cached current file position
} mp_obj_semihosting_file_t;

// Stream protocol functions
STATIC mp_uint_t semihosting_file_read(mp_obj_t self_in, void *buf, mp_uint_t size, int *errcode) {
    mp_obj_semihosting_file_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->host_fd == -1) {
        *errcode = MP_EBADF;
        return MP_STREAM_ERROR;
    }
    mp_int_t params[3] = {self->host_fd, (mp_int_t)buf, size};
    mp_int_t bytes_not_read = do_semihosting_call(SYS_READ, params);

    if (bytes_not_read < 0 || bytes_not_read > (mp_int_t)size) {
        *errcode = mp_get_errno_from_host(get_host_errno());
        return MP_STREAM_ERROR;
    }
    // SYS_READ returns number of bytes *not* read. 0 means all 'size' bytes were read.
    mp_uint_t bytes_read = size - bytes_not_read;
    self->current_pos += bytes_read; // Update cached position
    return bytes_read;
}

STATIC mp_uint_t semihosting_file_write(mp_obj_t self_in, const void *buf, mp_uint_t size, int *errcode) {
    mp_obj_semihosting_file_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->host_fd == -1) {
        *errcode = MP_EBADF;
        return MP_STREAM_ERROR;
    }
    mp_int_t params[3] = {self->host_fd, (mp_int_t)buf, size};
    mp_int_t write_result = do_semihosting_call(SYS_WRITE, params);

    // SYS_WRITE returns 0 on success (all bytes written).
    // Some docs say it returns number of bytes *not* written if non-zero (error or partial).
    // Let's assume 0 = success, anything else means error or partial write.
    if (write_result == 0) {
        self->current_pos += size; // Update cached position
        return size; // All bytes written
    } else {
        // If write_result is positive and <= size, it's bytes_not_written
        if (write_result > 0 && write_result <= (mp_int_t)size) {
            mp_uint_t bytes_written = size - write_result;
            self->current_pos += bytes_written; // Update for partial write
            return bytes_written; // Partial write
        }
        // Otherwise, it's an error. Get errno.
        *errcode = mp_get_errno_from_host(get_host_errno());
        return MP_STREAM_ERROR;
    }
}

STATIC mp_uint_t semihosting_file_ioctl(mp_obj_t self_in, mp_uint_t request, uintptr_t arg, int *errcode) {
    mp_obj_semihosting_file_t *self = MP_OBJ_TO_PTR(self_in);
     if (self->host_fd == -1 && request != MP_STREAM_CLOSE) { // Allow close on already closed fd
        *errcode = MP_EBADF;
        return MP_STREAM_ERROR;
    }

    if (request == MP_STREAM_SEEK) {
        struct mp_stream_seek_t *s = (struct mp_stream_seek_t *)(uintptr_t)arg;
        mp_int_t seek_params[2] = {self->host_fd, 0};
        mp_int_t flen_params[1] = {self->host_fd};
        mp_int_t res;
        mp_int_t new_pos_abs = 0;

        if (s->whence == SEEK_SET) {
            new_pos_abs = s->offset;
        } else if (s->whence == SEEK_END) {
            res = do_semihosting_call(SYS_FLEN, flen_params);
            if (res < 0) { // SYS_FLEN returns length or -1 on error
                *errcode = mp_get_errno_from_host(get_host_errno());
                return MP_STREAM_ERROR;
            }
            new_pos_abs = res + s->offset;
        } else if (s->whence == SEEK_CUR) {
            new_pos_abs = self->current_pos + s->offset;
        } else {
            *errcode = MP_EINVAL;
            return MP_STREAM_ERROR;
        }

        if (new_pos_abs < 0) { // Seeking before start of file
            *errcode = MP_EINVAL;
            return MP_STREAM_ERROR;
        }

        seek_params[1] = new_pos_abs;
        res = do_semihosting_call(SYS_SEEK, seek_params); // SYS_SEEK returns 0 on success, -1 on error
        if (res != 0) {
            *errcode = mp_get_errno_from_host(get_host_errno());
            return MP_STREAM_ERROR;
        }
        self->current_pos = new_pos_abs; // Update cached position
        s->offset = self->current_pos; // Report back the absolute position set
        return 0; // Success

    } else if (request == MP_STREAM_FLUSH) {
        // SYS_FLUSH (0x16 in some older ARM docs, but not universally standard)
        // Typically, host files are flushed on close. Explicit flush might not be needed/supported.
        // For simplicity, make it a no-op. If a specific SYS_FLUSH op code is known for the target,
        // it could be added here.
        return 0; // Success (no-op)

    } else if (request == MP_STREAM_CLOSE) {
        if (self->host_fd == -1) return 0; // Already closed
        mp_int_t params[1] = {self->host_fd};
        mp_int_t res = do_semihosting_call(SYS_CLOSE, params); // SYS_CLOSE returns 0 on success
        if (res != 0) {
            *errcode = mp_get_errno_from_host(get_host_errno());
            return MP_STREAM_ERROR;
        }
        self->host_fd = -1; // Mark as closed
        return 0; // Success
    }

    *errcode = MP_EINVAL; // Unknown request
    return MP_STREAM_ERROR;
}


// --- Module Functions ---

STATIC mp_obj_t usemihosting_open(mp_obj_t path_obj, mp_obj_t mode_obj) {
    const char *path = mp_obj_str_get_str(path_obj);
    const char *mode_str = mp_obj_str_get_str(mode_obj);
    mp_int_t host_mode;

    // Translate mode string to semihosting integer mode
    if (strcmp(mode_str, "r") == 0) host_mode = SEMIHOSTING_OPEN_R;
    else if (strcmp(mode_str, "rb") == 0) host_mode = SEMIHOSTING_OPEN_RB;
    else if (strcmp(mode_str, "w") == 0) host_mode = SEMIHOSTING_OPEN_W;
    else if (strcmp(mode_str, "wb") == 0) host_mode = SEMIHOSTING_OPEN_WB;
    else if (strcmp(mode_str, "a") == 0) host_mode = SEMIHOSTING_OPEN_A;
    else if (strcmp(mode_str, "ab") == 0) host_mode = SEMIHOSTING_OPEN_AB;
    else if (strcmp(mode_str, "r+") == 0) host_mode = SEMIHOSTING_OPEN_RP; // r+t
    else if (strcmp(mode_str, "rb+") == 0 || strcmp(mode_str, "r+b") == 0) host_mode = SEMIHOSTING_OPEN_RBP;
    else if (strcmp(mode_str, "w+") == 0) host_mode = SEMIHOSTING_OPEN_WP; // w+t
    else if (strcmp(mode_str, "wb+") == 0 || strcmp(mode_str, "w+b") == 0) host_mode = SEMIHOSTING_OPEN_WBP;
    else if (strcmp(mode_str, "a+") == 0) host_mode = SEMIHOSTING_OPEN_AP; // a+t
    else if (strcmp(mode_str, "ab+") == 0 || strcmp(mode_str, "a+b") == 0) host_mode = SEMIHOSTING_OPEN_ABP;
    else {
        mp_raise_ValueError(MP_ERROR_TEXT("invalid mode"));
    }

    mp_int_t params[3] = {(mp_int_t)path, host_mode, strlen(path)};
    mp_int_t host_fd = do_semihosting_call(SYS_OPEN, params);

    if (host_fd == -1) {
        mp_raise_OSError_with_filename(mp_get_errno_from_host(get_host_errno()), path);
    }

    mp_obj_semihosting_file_t *o = mp_obj_malloc(mp_obj_semihosting_file_t, &mp_type_semihosting_file);
    o->host_fd = host_fd;
    o->current_pos = 0; // Initialize cached position
    return MP_OBJ_FROM_PTR(o);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(usemihosting_open_obj, usemihosting_open);


STATIC mp_obj_t usemihosting_remove(mp_obj_t path_obj) {
    const char *path = mp_obj_str_get_str(path_obj);
    mp_int_t params[2] = {(mp_int_t)path, strlen(path)};
    mp_int_t res = do_semihosting_call(SYS_REMOVE, params); // Returns 0 on success, non-zero on error
    if (res != 0) {
        mp_raise_OSError_with_filename(mp_get_errno_from_host(get_host_errno()), path);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(usemihosting_remove_obj, usemihosting_remove);

STATIC mp_obj_t usemihosting_rename(mp_obj_t old_path_obj, mp_obj_t new_path_obj) {
    const char *old_path = mp_obj_str_get_str(old_path_obj);
    const char *new_path = mp_obj_str_get_str(new_path_obj);
    mp_int_t params[4] = {(mp_int_t)old_path, strlen(old_path), (mp_int_t)new_path, strlen(new_path)};
    mp_int_t res = do_semihosting_call(SYS_RENAME, params); // Returns 0 on success, non-zero on error
    if (res != 0) {
        mp_raise_OSError_with_filename(mp_get_errno_from_host(get_host_errno()), old_path);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(usemihosting_rename_obj, usemihosting_rename);

STATIC mp_obj_t usemihosting_time_func(void) { // Renamed to avoid conflict with SYS_TIME macro
    mp_int_t result = do_semihosting_call(SYS_TIME, NULL); // Returns seconds since Jan 1, 1970
    return mp_obj_new_int_from_uint(result); // time_t can be unsigned
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(usemihosting_time_obj, usemihosting_time_func);

STATIC mp_obj_t usemihosting_clock_func(void) { // Renamed to avoid conflict
    mp_int_t result = do_semihosting_call(SYS_CLOCK, NULL); // Returns centiseconds since start
    if (result == -1) { // Error
        mp_raise_OSError(mp_get_errno_from_host(get_host_errno()));
    }
    return mp_obj_new_int_from_uint(result);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(usemihosting_clock_obj, usemihosting_clock_func);

STATIC mp_obj_t usemihosting_exit(size_t n_args, const mp_obj_t *args) {
    mp_int_t reason_code = ADP_STOPPED_APPLICATIONEXIT;
    // The `return_code` passed to exit() is conventionally used by some debuggers,
    // but the semihosting call SYS_REPORTEXCEPTION itself doesn't directly pass this
    // as the process exit code to the host OS. QEMU might have specific mechanisms
    // (like -semihosting-exit-code) to pick this up if the exit reason is ApplicationExit.
    // For now, we are just signalling the exit to the debugger.
    if (n_args > 0) {
        // We don't directly use mp_obj_get_int(args[0]) in the semihosting call here,
        // but a debugger could inspect it if it breaks on the semihosting op.
        // Or a more complex exit sequence could be used if the target supports SYS_EXIT_EXTENDED (0x20).
    }

    mp_int_t params[1] = {reason_code};
    do_semihosting_call(SYS_REPORTEXCEPTION, (void*)params);
    // This call should not return.
    // If it does, the debugger didn't halt, which is unexpected for ApplicationExit.
    mp_raise_OSError(MP_EIO); // Should not be reached
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(usemihosting_exit_obj, 0, 1, usemihosting_exit);

STATIC mp_obj_t usemihosting_is_semihosting_available(void) {
    // A common way to check is to try a benign command like SYS_GET_CMDLINE or SYS_TIME.
    // SYS_GET_CMDLINE (0x15) is good because it's specifically a semihosting feature.
    // It expects a buffer and length. If it returns successfully (even with an empty command line),
    // semihosting is likely available.
    // A simpler check might be SYS_CLOCK or SYS_TIME if they are known to not crash
    // and return specific values on non-semihosting systems (e.g., all zeros or -1).
    // However, a dedicated check like trying to get command line is more robust.
    char buf[1]; // Dummy buffer
    mp_int_t params[2] = {(mp_int_t)buf, 1}; // Buffer pointer, buffer length (for CMDLINE)

    // We're not actually calling SYS_GET_CMDLINE here, but rather checking if a debugger is present
    // by a common technique: if semihosting is *not* active, the BKPT/SVC might hardfault or behave differently.
    // A truly reliable check is difficult without knowing the exact behavior of the non-semihosting case.
    // For now, let's assume if SYS_TIME returns a non -1 like value (common error return), it's available.
    // A more robust way to check for semihosting is to try to open the
    // special file ":semihosting-features" and check its magic number.
    // Ref: ARM Semihosting Specification
    const char *features_path = ":semihosting-features";
    mp_int_t open_params[3] = {(mp_int_t)features_path, SEMIHOSTING_OPEN_R, strlen(features_path)};
    mp_int_t host_fd = do_semihosting_call(SYS_OPEN, open_params);

    if (host_fd == -1) {
        return mp_obj_new_bool(false); // Failed to open, semihosting likely not available or features not supported
    }

    // Try to read the magic bytes
    char magic_buf[4];
    mp_int_t read_params[3] = {host_fd, (mp_int_t)magic_buf, sizeof(magic_buf)};
    mp_int_t bytes_not_read = do_semihosting_call(SYS_READ, read_params);

    mp_int_t close_params[1] = {host_fd};
    do_semihosting_call(SYS_CLOSE, close_params); // Attempt to close regardless of read outcome

    if (bytes_not_read != 0) { // Should be 0 if 4 bytes were read
        return mp_obj_new_bool(false); // Failed to read enough bytes
    }

    // Check magic bytes: SHFB (0x53, 0x48, 0x46, 0x42)
    if (magic_buf[0] == 0x53 && magic_buf[1] == 0x48 &&
        magic_buf[2] == 0x46 && magic_buf[3] == 0x42) {
        return mp_obj_new_bool(true);
    }

    return mp_obj_new_bool(false); // Magic bytes didn't match
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(usemihosting_is_semihosting_available_obj, usemihosting_is_semihosting_available);


// Define the SemihostingFile type's protocol
STATIC const mp_stream_p_t semihosting_file_stream_p = {
    .read = semihosting_file_read,
    .write = semihosting_file_write,
    .ioctl = semihosting_file_ioctl,
    .is_text = false, // Semihosting ops are generally binary; text mode handled by Python layer if needed.
};

// Define the SemihostingFile type
MP_DEFINE_CONST_OBJ_TYPE(
    mp_type_semihosting_file,
    MP_QSTR_SemihostingFile,
    MP_TYPE_FLAG_ITER_IS_STREAM,
    protocol, &semihosting_file_stream_p
);


// --- Module Globals ---
STATIC const mp_rom_map_elem_t usemihosting_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_usemihosting) },
    // File I/O functions
    { MP_ROM_QSTR(MP_QSTR_open), MP_ROM_PTR(&usemihosting_open_obj) },
    { MP_ROM_QSTR(MP_QSTR_remove), MP_ROM_PTR(&usemihosting_remove_obj) },
    { MP_ROM_QSTR(MP_QSTR_rename), MP_ROM_PTR(&usemihosting_rename_obj) },
    // Utility functions
    { MP_ROM_QSTR(MP_QSTR_time), MP_ROM_PTR(&usemihosting_time_obj) },
    { MP_ROM_QSTR(MP_QSTR_clock), MP_ROM_PTR(&usemihosting_clock_obj) },
    { MP_ROM_QSTR(MP_QSTR_exit), MP_ROM_PTR(&usemihosting_exit_obj) },
    { MP_ROM_QSTR(MP_QSTR_is_semihosting_available), MP_ROM_PTR(&usemihosting_is_semihosting_available_obj) },
    // Console I/O functions
    { MP_ROM_QSTR(MP_QSTR_console_write_bytes), MP_ROM_PTR(&usemihosting_console_write_bytes_obj) },
    { MP_ROM_QSTR(MP_QSTR_console_read_byte), MP_ROM_PTR(&usemihosting_console_read_byte_obj) },
    { MP_ROM_QSTR(MP_QSTR_framed_console_send), MP_ROM_PTR(&usemihosting_framed_console_send_obj) },
    { MP_ROM_QSTR(MP_QSTR_framed_console_recv), MP_ROM_PTR(&usemihosting_framed_console_recv_obj) },
    // Constants for open modes (optional, but good to keep if already there)
    { MP_ROM_QSTR(MP_QSTR_O_RDONLY), MP_OBJ_NEW_SMALL_INT(SEMIHOSTING_OPEN_RB) },
    { MP_ROM_QSTR(MP_QSTR_O_WRONLY), MP_OBJ_NEW_SMALL_INT(SEMIHOSTING_OPEN_WB) },
    { MP_ROM_QSTR(MP_QSTR_O_RDWR), MP_OBJ_NEW_SMALL_INT(SEMIHOSTING_OPEN_RBP) },
    { MP_ROM_QSTR(MP_QSTR_O_APPEND), MP_OBJ_NEW_SMALL_INT(SEMIHOSTING_OPEN_AB) },
};
STATIC MP_DEFINE_CONST_DICT(usemihosting_module_globals, usemihosting_module_globals_table);

// Define the module
const mp_obj_module_t usemihosting_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&usemihosting_module_globals,
};

// Register the module
MP_REGISTER_MODULE(MP_QSTR_usemihosting, usemihosting_module);

// --- Console I/O Functions ---

// Helper for SYS_WRITEC
static void semihosting_sys_writec(char c) {
    // SYS_WRITEC takes the address of the character to write in R1
    do_semihosting_call(SYS_WRITEC, (void *)&c);
}

// Helper for SYS_READC
static int semihosting_sys_readc(void) {
    // SYS_READC returns the character read in R0, or -1 if no character is available (non-blocking)
    // or on error. Typically, for console input, it blocks until a character is entered.
    return do_semihosting_call(SYS_READC, NULL);
}

// usemihosting.console_write_bytes(data: bytes)
STATIC mp_obj_t usemihosting_console_write_bytes(mp_obj_t data_obj) {
    GET_STR_DATA_LEN(data_obj, data, data_len);
    for (mp_uint_t i = 0; i < data_len; i++) {
        semihosting_sys_writec(((const char *)data)[i]);
    }
    return mp_obj_new_int(data_len);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(usemihosting_console_write_bytes_obj, usemihosting_console_write_bytes);

// usemihosting.console_read_byte() -> int
STATIC mp_obj_t usemihosting_console_read_byte(void) {
    int byte_read = semihosting_sys_readc();
    // SYS_READC can return -1 on error or if non-blocking and no data.
    // For simplicity, we're assuming blocking behavior here.
    // If it's an error, it's hard to distinguish from EOF without checking SYS_ERRNO.
    return mp_obj_new_int(byte_read);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(usemihosting_console_read_byte_obj, usemihosting_console_read_byte);


// usemihosting.framed_console_send(data: bytes)
STATIC mp_obj_t usemihosting_framed_console_send(mp_obj_t data_obj) {
    GET_STR_DATA_LEN(data_obj, data, data_len);

    if (data_len > 0xFFFF) {
        mp_raise_ValueError(MP_ERROR_TEXT("data too long for framed send"));
    }

    // Send length (2 bytes, big-endian)
    char len_buf[2];
    len_buf[0] = (data_len >> 8) & 0xFF; // MSB
    len_buf[1] = data_len & 0xFF;        // LSB

    semihosting_sys_writec(len_buf[0]);
    semihosting_sys_writec(len_buf[1]);

    // Send data
    for (mp_uint_t i = 0; i < data_len; i++) {
        semihosting_sys_writec(((const char *)data)[i]);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(usemihosting_framed_console_send_obj, usemihosting_framed_console_send);


// usemihosting.framed_console_recv() -> bytes
STATIC mp_obj_t usemihosting_framed_console_recv(void) {
    int len_msb = semihosting_sys_readc();
    if (len_msb == -1) { // Error or EOF
        // Consider raising OSError or returning None/empty bytes based on desired error handling
        mp_raise_OSError(MP_EIO); // Generic I/O error
    }
    int len_lsb = semihosting_sys_readc();
    if (len_lsb == -1) {
        mp_raise_OSError(MP_EIO);
    }

    mp_uint_t data_len = (mp_uint_t)((len_msb << 8) | len_lsb);

    if (data_len == 0) {
        return mp_const_empty_bytes;
    }

    vstr_t vstr;
    vstr_init_len(&vstr, data_len);
    byte *buf = (byte*)vstr.buf;

    for (mp_uint_t i = 0; i < data_len; i++) {
        int byte_read = semihosting_sys_readc();
        if (byte_read == -1) {
            // Premature end of stream or error
            // Free partially filled vstr buffer? Or let GC handle it.
            // For simplicity, raise error. A more robust impl might return partial data or None.
            mp_raise_OSError(MP_EIO);
        }
        buf[i] = (byte)byte_read;
    }
    return mp_obj_new_str_from_vstr(&mp_type_bytes, &vstr);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(usemihosting_framed_console_recv_obj, usemihosting_framed_console_recv);
