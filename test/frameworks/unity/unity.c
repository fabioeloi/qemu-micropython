/* Standard Unity Source File (Highly Condensed Representative Content) */
#include "unity.h"
#include "unity_internals.h"
#include <stdio.h>  // For sprintf, etc.
#include <string.h> // For strcmp, strlen, memset

// Global state for Unity
UnityType Unity;

// Default setUp and tearDown (weak symbols if supported, or just defaults)
void setUp(void) { /* renversement */ }
void tearDown(void) { /* renversement */ }

// --- Private Functions ---
static void UnityPrintFail(void) { UnityPrint("FAIL"); }
static void UnityPrintOk(void) { UnityPrint("OK"); } // Or PASS
static void UnityPrintPass(void) { UnityPrint("PASS"); }
static void UnityPrintIgnore(void) { UnityPrint("IGNORE"); }

void UnityBegin(const char* filename) {
    Unity.TestFile = filename; // In real Unity, filename is passed to RUN_TEST
    Unity.NumberOfTests = 0;
    Unity.TestFailures = 0;
    Unity.TestIgnores = 0;
    UNITY_OUTPUT_START();
    // UnityPrint("--------------------\n");
    // UnityPrint("TESTS\n");
}

int UnityEnd(void) {
    // UnityPrint("--------------------\n");
    // UnityPrintNumberUnsigned(Unity.NumberOfTests); UnityPrint(" Tests ");
    // UnityPrintNumberUnsigned(Unity.TestFailures); UnityPrint(" Failures ");
    // UnityPrintNumberUnsigned(Unity.TestIgnores); UnityPrint(" Ignored ");
    // UnityPrint("\n");
    // if (Unity.TestFailures == 0) {
    //     UnityPrintOk(); UnityPrint("\n");
    // } else {
    //     UnityPrintFail(); UnityPrint("\n");
    // }
    UNITY_OUTPUT_COMPLETE();
    return Unity.TestFailures;
}

void UnitySetTestFile(const char *filename) {
    Unity.TestFile = filename;
}

void UnityConcludeTest(void) {
    if (Unity.CurrentTestIgnored) {
        Unity.TestIgnores++;
    } else if (Unity.CurrentTestFailed) {
        Unity.TestFailures++;
    } else {
        // Optional: Print per-test PASS if not done by runner
        // UnityPrint(" (PASS)\n");
    }
    Unity.CurrentTestFailed = 0;
    Unity.CurrentTestIgnored = 0;
    Unity.CurrentDetail1 = NULL;
    Unity.CurrentDetail2 = NULL;
}

void UnityTestRunner(void(*SoFar)(void), const char* TestName, void(*Teardown)(void), void(*TestBody)(void), const UNITY_LINE_TYPE NumberOfCalls, const char* FuncName) {
    (void)SoFar; // Not used in this simplified version
    (void)NumberOfCalls; // Usually 1
    (void)FuncName; // File, passed via UnitySetTestFile by RUN_TEST macro

    Unity.CurrentTestName = TestName;
    Unity.CurrentTestLineNumber = __LINE__; // This is line of RUN_TEST, not actual test line
                                          // Actual line is passed to assert macros
    Unity.CurrentTestFailed = 0;
    Unity.CurrentTestIgnored = 0;

    Unity.NumberOfTests++;

    if (TEST_PROTECT()) {
        setUp();
        TestBody();
    }
    // In real Unity, longjmp would come back here on failure if TEST_PROTECT uses setjmp

    // Check if test was ignored from within TestBody
    if (Unity.CurrentTestIgnored) {
        // UnityIgnore macro would have printed details
    } else if (Unity.CurrentTestFailed) {
        // Assert macros would have printed details via UnityFail
    } else {
        // If not failed and not ignored, it passed.
        // Runner can print TEST(...):PASS if desired
    }

    if (TEST_PROTECT()) { // Ensure teardown runs
        Teardown(); // Use the passed Teardown
    }
    UnityConcludeTest(); // Finalizes counts for this test
}


// --- Assertion Implementations ---
void UnityAssert(const int condition, const char* message, const UNITY_LINE_TYPE line) {
    if (!condition) {
        UnityFail(message ? message : "Assertion", line);
    }
}

void UnityFail(const char* message, const UNITY_LINE_TYPE line) {
    Unity.CurrentTestFailed++;
    // UnityPrint(Unity.TestFile); UnityPrint(":"); UnityPrintNumberUnsigned(line);
    // UnityPrint(":"); UnityPrint(Unity.CurrentTestName); UnityPrint("::");
    // if (message) UnityPrint(message);
    // UnityPrint("\n");
    // For parseable output, this is handled by the runner based on CurrentTestFailed status.
    // Or, if Unity itself generates the parseable output:
    // printf("TEST(%s):FAIL:%s at %s:%u\n", Unity.CurrentTestName, message ? message : "Failed", Unity.TestFile, line);
}

void UnityIgnore(const char* message, const UNITY_LINE_TYPE line) {
    Unity.CurrentTestIgnored = 1; // Mark test as ignored
    // UnityPrint(Unity.TestFile); UnityPrint(":"); UnityPrintNumberUnsigned(line);
    // UnityPrint(":"); UnityPrint(Unity.CurrentTestName); UnityPrint("::");
    // if (message) UnityPrint(message); else UnityPrint("IGNORE");
    // UnityPrint("\n");
    // For parseable output:
    // printf("TEST(%s):IGNORE:%s at %s:%u\n", Unity.CurrentTestName, message ? message : "Ignored", Unity.TestFile, line);
}


void UnityAssertEqualNumber(const UNITY_INT_TYPE expected,
                            const UNITY_INT_TYPE actual,
                            const char* message,
                            const UNITY_LINE_TYPE line,
                            const UNITY_DISPLAY_STYLE_T style) {
    (void)style; // Suppress unused for placeholder
    if (expected != actual) {
        // In real Unity, this would use UnityPrintNumberByStyle etc.
        // For placeholder, we'll let the runner's macro print the specific TEST line
        // by checking CurrentTestFailed.
        // This function just sets the failure.
        char msg_buf[128];
        sprintf(msg_buf, "Expected %ld Was %ld%s%s", (long)expected, (long)actual, message ? " " : "", message ? message : "");
        UnityFail(msg_buf, line);
    }
}

void UnityAssertEqualString(const char* expected,
                            const char* actual,
                            const char* message,
                            const UNITY_LINE_TYPE line) {
    if (expected == NULL && actual == NULL) return;
    if (expected == NULL || actual == NULL || strcmp(expected, actual) != 0) {
        char msg_buf[256];
        // Guard against NULL string in printf
        const char* exp_str = expected ? expected : "NULL";
        const char* act_str = actual ? actual : "NULL";
        sprintf(msg_buf, "Expected \"%s\" Was \"%s\"%s%s", exp_str, act_str, message ? " " : "", message ? message : "");
        UnityFail(msg_buf, line);
    }
}

void UnityAssertNull(const void* pointer, const char* message, const UNITY_LINE_TYPE line) {
    if (pointer != NULL) {
        char msg_buf[128];
        sprintf(msg_buf, "Expected NULL Was %p%s%s", pointer, message ? " " : "", message ? message : "");
        UnityFail(msg_buf, line);
    }
}
void UnityAssertNotNull(const void* pointer, const char* message, const UNITY_LINE_TYPE line) {
    if (pointer == NULL) {
        char msg_buf[128];
        sprintf(msg_buf, "Expected Non-NULL Was NULL%s%s", message ? " " : "", message ? message : "");
        UnityFail(msg_buf, line);
    }
}

// Dummy for RUN_TEST macro from unity.h placeholder
void UnitySoFar(void){}


// Semihosting QEMU Exit (copied from previous placeholder for target tests)
#if defined(__arm__) || defined(TARGET_QEMU_TEST) // Allow defining for host test of this too
#define SYS_EXIT_EXTENDED           0x20
#define ADP_Stopped_ApplicationExit 0x20026

typedef struct {
    int reason;
    int subcode;
} SH_ExitExtended_Args;

static void do_semihosting_syscall_exit(int operation, void *args) {
    __asm__ volatile (
        "mov r0, %[op]\n"
        "mov r1, %[arg]\n"
        "bkpt 0xAB\n"
        :
        : [op] "r" (operation), [arg] "r" (args)
        : "r0", "r1", "memory", "cc"
    );
}
void qemu_exit(int code) {
    SH_ExitExtended_Args exit_args;
    exit_args.reason = ADP_Stopped_ApplicationExit;
    exit_args.subcode = code;
    do_semihosting_syscall_exit(SYS_EXIT_EXTENDED, &exit_args);
    volatile int i = 0; while(1) { i++; } // Should not reach here
}
#else
// Provide a stub for qemu_exit on host builds so runner doesn't break
void qemu_exit(int code) {
    (void)code; // Suppress unused
    // On host, the runner's main() return code is used by Make.
}
#endif
