#include "unity.h" // Uses the new representative unity.h
#include <stdio.h>  // For printf for the PASS line

// If compiled for ARM target, ensure qemu_exit is available
#if defined(__arm__) || defined(TARGET_QEMU_TEST)
void qemu_exit(int code);
#endif

// Forward declarations of test functions from test_string_utils.c
void test_is_string_empty_null_string(void);
void test_is_string_empty_empty_string(void);
void test_is_string_empty_non_empty_string(void);
void test_is_string_empty_string_with_spaces(void);

void test_reverse_string_null(void);
void test_reverse_string_empty(void);
void test_reverse_string_single_char(void);
void test_reverse_string_even_length(void);
void test_reverse_string_odd_length(void);
void test_reverse_string_palindrome(void);
void test_reverse_string_with_spaces(void);

// setUp and tearDown are defined in test_string_utils.c and called by Unity's RUN_TEST logic.
// No need for stubs here if test_string_utils.c provides them (even if empty).
// The representative unity.c provides weak-like default empty setUp/tearDown.

// Custom RUN_TEST wrapper to print PASS message for our parseable output
// This macro will call the standard Unity RUN_TEST (which might be a bit simplified in our placeholder)
// and then check the result for THIS test to print PASS if needed.
// Note: Real Unity's RUN_TEST macro is complex. This MY_RUN_TEST assumes a simplified
// interaction with the global Unity structure for failure/ignore counts specific to the test run.
#define MY_RUN_TEST(test_func_name) do { \
    Unity.CurrentTestName = #test_func_name; \
    Unity.CurrentTestLineNumber = (UNITY_LINE_TYPE)__LINE__; /* Line of this RUN_TEST call */ \
    Unity.CurrentTestFailed = 0; \
    Unity.CurrentTestIgnored = 0; \
    \
    UnityDefaultTestRun(test_func_name, #test_func_name, (UNITY_LINE_TYPE)__LINE__); \
    \
    /* UnityDefaultTestRun would call UnityConcludeTest which updates global counts */ \
    /* For parseable output, UnityFail and UnityIgnore in placeholder unity.c now print */ \
    /* TEST(...):FAIL... and TEST(...):IGNORE... lines. */ \
    /* So, we only need to print TEST(...):PASS if it wasn't failed or ignored. */ \
    if (!Unity.CurrentTestFailed && !Unity.CurrentTestIgnored) { \
        printf("TEST(%s):PASS\n", #test_func_name); \
    } \
    /* UnityConcludeTest is effectively called by UnityDefaultTestRun or its internals */ \
    /* In our placeholder, UnityDefaultTestRun itself increments Unity.NumberOfTests */ \
    /* and UnityConcludeTest would just finalize state for that test based on CurrentTestFailed/Ignored */ \
    /* Let's ensure CurrentTestFailed/Ignored are reset for the next MY_RUN_TEST if UnityConcludeTest doesn't */ \
    /* Actually, UnityConcludeTest is better called inside UnityDefaultTestRun or by the main RUN_TEST macro. */ \
    /* The placeholder unity.c's UnityDefaultTestRun calls setUp, test, tearDown. */ \
    /* UnityFail/UnityIgnore set CurrentTestFailed/Ignored and print. */
    /* UnityDefaultTestRun then needs to call UnityConcludeTest. */
    /* Let's assume our placeholder UnityDefaultTestRun is now: */
    /* void UnityDefaultTestRun(void (*pF)(void), const char* N, const UNINT L) { */
    /*   Unity.NumberOfTests++; Unity.CurrentTestFailed=0; Unity.CurrentTestIgnored=0; */
    /*   setUp(); pF(); tearDown(); */
    /*   if(Unity.CurrentTestFailed) {print FAIL} else if (Unity.CurrentTestIgnored) {print IGNORE} else {print PASS for this runner} */
    /*   UnityConcludeTest(); // which updates global Unity.TestFailures etc. */
    /* } */
    /* The current placeholder unity.c has UnityDefaultTestRun incrementing NumberOfTests. */
    /* Assertions call UnityFailHandler (prints FAIL line, increments global UnityFailureCount). */
    /* UnityIgnore prints IGNORE line, increments global UnityIgnoreCount. */
    /* So, the runner just needs to print PASS if neither of those happened for the current test. */
    /* This requires checking if UnityFailureCount/UnityIgnoreCount *increased* due to this test. */
    unsigned int failures_before = Unity.TestFailures; \
    unsigned int ignores_before = Unity.TestIgnores; \
    UnityDefaultTestRun(test_func_name, #test_func_name, (UNITY_LINE_TYPE)__LINE__); \
    if (Unity.TestIgnores == ignores_before && Unity.TestFailures == failures_before) { \
        printf("TEST(%s):PASS\n", #test_func_name); \
    } \
} while(0)


int main(void) {
    UNITY_BEGIN();

    MY_RUN_TEST(test_is_string_empty_null_string);
    MY_RUN_TEST(test_is_string_empty_empty_string);
    MY_RUN_TEST(test_is_string_empty_non_empty_string);
    MY_RUN_TEST(test_is_string_empty_string_with_spaces);

    MY_RUN_TEST(test_reverse_string_null);
    MY_RUN_TEST(test_reverse_string_empty);
    MY_RUN_TEST(test_reverse_string_single_char);
    MY_RUN_TEST(test_reverse_string_even_length);
    MY_RUN_TEST(test_reverse_string_odd_length);
    MY_RUN_TEST(test_reverse_string_palindrome);
    MY_RUN_TEST(test_reverse_string_with_spaces);

    int overall_result = UNITY_END(); // Prints SUMMARY line and returns failure count (0 for pass)

#if defined(__arm__) || defined(TARGET_QEMU_TEST)
    qemu_exit(overall_result);
#endif

    return overall_result;
}
