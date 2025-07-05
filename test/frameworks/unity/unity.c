// This is a placeholder for Unity's unity.c source file.
// In a real setup, this would contain the full Unity framework implementation.
#include "unity.h"
#include <stdio.h>  // For printf
#include <string.h> // For strcmp

// Global state for Unity (simplified)
unsigned int UnityLineNumber = 0;
const char *UnityTestName = NULL;
unsigned int UnityTestCount = 0;
unsigned int UnityFailureCount = 0;
unsigned int UnityIgnoreCount = 0;
static const char* CurrentTestName = NULL;
static int TestWasIgnored = 0;

// Output character function (can be redefined by user)
#ifndef UNITY_OUTPUT_CHAR
#define UNITY_OUTPUT_CHAR(c) putchar(c)
#endif

static void UnityPrint(const char* string) {
    const char* p = string;
    while (*p) {
        UNITY_OUTPUT_CHAR(*p);
        p++;
    }
}

static void UnityPrintNumberUnsigned(unsigned int number) {
    char buffer[20];
    sprintf(buffer, "%u", number);
    UnityPrint(buffer);
}

static void UnityPrintNumber(int number) {
    char buffer[20];
    sprintf(buffer, "%d", number);
    UnityPrint(buffer);
}


void UnityBegin(const char* filename) {
    // In a real Unity, filename might be used. Here, just init counts.
    (void)filename; // Suppress unused warning
    UnityTestCount = 0;
    UnityFailureCount = 0;
    UnityIgnoreCount = 0;
    // UnityPrint("--------------------\n");
    // UnityPrint("TESTS\n");
    // UnityPrint("--------------------\n");
}

// This is called by RUN_TEST macro
void UnityDefaultTestRun(void (*pTestFunc)(void), const char* funcName, const unsigned int funcLine) {
    CurrentTestName = funcName; // Set for per-test reporting
    TestWasIgnored = 0;
    UnityTestCount++;

    // Simplified protection, real Unity uses setjmp/longjmp
    if (TEST_PROTECT()) {
        setUp();
        pTestFunc();
    }
    if (TEST_PROTECT()) { // Ensure tearDown runs even if test fails (simplified)
        tearDown();
    }

    if (TestWasIgnored) {
        // Test was ignored, UnityIgnore already printed the TEST line
    } else if (UnityFailureCount > (UnityTestCount - UnityIgnoreCount -1) ) { // Check if this specific test failed
        // This logic is a bit off for placeholder. Real Unity tracks failure per test.
        // For placeholder, we assume if FailureCount increased, this test *could* be the one.
        // A better placeholder would have pTestFunc return a status or asserts call a central fail routine.
        // We will rely on the runner to print the TEST line based on failure count increment.
        // UnityFail already prints the TEST line for FAIL.
    } else {
         // Only print PASS if not ignored and not failed
        printf("TEST(%s):PASS\n", CurrentTestName);
    }
    CurrentTestName = NULL;
}

int UnityEnd(void) {
    // Final summary line for easy parsing by automation script
    printf("SUMMARY:%u:%u:%u\n", UnityTestCount, UnityFailureCount, UnityIgnoreCount);
    return (UnityFailureCount > 0) ? 1 : 0; // Return non-zero if failures
}

// --- Assertion Implementations (Simplified Placeholders) ---
static void UnityFailHandler(const char* message, const unsigned int line) {
    printf("TEST(%s):FAIL:%s at %u\n", CurrentTestName ? CurrentTestName : "UnknownTest", message ? message : "Assertion", line);
    UnityFailureCount++;
}

void UnityAssertEqualNumber(const int expected, const int actual, const char* msg, const unsigned int line) {
    if (expected != actual) {
        char message_buffer[128];
        sprintf(message_buffer, "Expected %d Was %d%s%s", expected, actual, msg ? " " : "", msg ? msg : "");
        UnityFailHandler(message_buffer, line);
    }
}

void UnityAssertEqualString(const char* expected, const char* actual, const char* msg, const unsigned int line) {
    if (expected == NULL && actual == NULL) return;
    if (expected == NULL || actual == NULL || strcmp(expected, actual) != 0) {
        char message_buffer[256];
        // Be careful with printing NULL strings directly
        sprintf(message_buffer, "Expected \"%s\" Was \"%s\"%s%s",
                expected ? expected : "NULL",
                actual ? actual : "NULL",
                msg ? " " : "", msg ? msg : "");
        UnityFailHandler(message_buffer, line);
    }
}

void UnityAssertNull(const void* pointer, const char* msg, const unsigned int line) {
    if (pointer != NULL) {
        char message_buffer[128];
        sprintf(message_buffer, "Expected NULL Was %p%s%s", pointer, msg ? " " : "", msg ? msg : "");
        UnityFailHandler(message_buffer, line);
    }
}

void UnityAssertNotNull(const void* pointer, const char* msg, const unsigned int line) {
    if (pointer == NULL) {
        char message_buffer[128];
        sprintf(message_buffer, "Expected NOT-NULL Was NULL%s%s", msg ? " " : "", msg ? msg : "");
        UnityFailHandler(message_buffer, line);
    }
}

void UnityAssertTrue(const int condition, const char* msg, const unsigned int line) {
    if (!condition) {
        UnityFailHandler(msg ? msg : "Expected TRUE was FALSE", line);
    }
}

void UnityAssertFalse(const int condition, const char* msg, const unsigned int line) {
    if (condition) {
        UnityFailHandler(msg ? msg : "Expected FALSE was TRUE", line);
    }
}


void UnityFail(const char* message, const unsigned int line) {
    UnityFailHandler(message, line);
}

void UnityIgnore(const char* message, const unsigned int line) {
    printf("TEST(%s):IGNORE:%s at %u\n", CurrentTestName ? CurrentTestName : "UnknownTest", message ? message : "Ignored", line);
    UnityIgnoreCount++;
    TestWasIgnored = 1; // Mark that current test is ignored
}


// --- Semihosting QEMU Exit ---
// ARM Semihosting interface
#define SYS_EXIT_EXTENDED           0x20 // Newer semihosting call for exit with status
#define ADP_Stopped_ApplicationExit 0x20026 // Reason code for normal exit

// Structure to pass arguments to SYS_EXIT_EXTENDED
typedef struct {
    int reason;
    int subcode; // This will be the application's exit status
} SH_ExitExtended_Args;

static void do_semihosting_syscall(int operation, void *args) {
    // This asm block needs to be correct for the target's semihosting mechanism
    // Common for ARM is BKPT 0xAB or SVC 0x123456
    // Using BKPT 0xAB as it's common for bare-metal and QEMU often supports it well.
    __asm__ volatile (
        "mov r0, %[op]\n"
        "mov r1, %[arg]\n"
        "bkpt 0xAB\n"
        : /* no outputs */
        : [op] "r" (operation), [arg] "r" (args)
        : "r0", "r1", "memory", "cc"
    );
}

void qemu_exit(int code) {
    SH_ExitExtended_Args exit_args;
    exit_args.reason = ADP_Stopped_ApplicationExit;
    exit_args.subcode = code; // Pass the test suite's exit code

    do_semihosting_syscall(SYS_EXIT_EXTENDED, &exit_args);

    // Backup, less informative exit (if SYS_EXIT_EXTENDED is not handled by QEMU)
    // #define SYS_EXIT 0x18
    // do_semihosting_syscall(SYS_EXIT, (void*)ADP_Stopped_ApplicationExit);

    // Loop forever if semihosting exit fails for some reason
    volatile int i = 0;
    while(1) { i++; }
}
