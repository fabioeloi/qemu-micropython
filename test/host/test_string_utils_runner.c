// This runner is for HOST execution.
// For QEMU TARGET execution, we will need a different runner or this one
// adapted further if it's compiled with arm-none-eabi-gcc.
// The main difference for target will be the inclusion of qemu_exit().

#include "unity.h"
#include <stdio.h> // For final summary printf if not handled by UnityEnd

// If this runner is also to be used for on-target QEMU tests, qemu_exit must be available.
// For host-only, it's not needed. The plan is to make this runner work for target.
#if defined(__arm__) // Or some other macro indicating ARM target compilation
// Only declare qemu_exit for ARM target builds
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

// setUp and tearDown are expected by the UnityDefaultTestRun in placeholder unity.c
// They should be defined in test_string_utils.c if needed per-test,
// or these empty ones will be linked if test_string_utils.c doesn't provide them.
// Ensure only one definition if linking multiple .c files for a test executable.
// Best practice: define them (even if empty) in the file with the tests (test_string_utils.c).
// These are here as a fallback if that file doesn't link them for some reason (unlikely with typical make).
#ifndef TEST_SETUP_DEFINED_IN_TEST_FILE
void setUp(void) { /* Default empty */ }
#endif
#ifndef TEST_TEARDOWN_DEFINED_IN_TEST_FILE
void tearDown(void) { /* Default empty */ }
#endif


int main(void) {
    UNITY_BEGIN();

    // For our placeholder Unity, RUN_TEST calls UnityDefaultTestRun which increments UnityTestCount.
    // Assertions call UnityFailHandler which prints the TEST(...):FAIL line and increments UnityFailureCount.
    // If a test function completes without UnityFailureCount increasing for it, we print TEST(...):PASS.
    // This is more manual than real Unity.

    unsigned int initial_failures;
    unsigned int initial_ignores; // Assuming UnityIgnoreCount is tracked

#define RUN_TEST_WITH_PARSABLE_OUTPUT(test_func) do { \
        initial_failures = UnityFailureCount; \
        initial_ignores = UnityIgnoreCount; \
        UnityDefaultTestRun(test_func, #test_func, (unsigned int)__LINE__); \
        if (UnityIgnoreCount > initial_ignores) { \
            /* UnityIgnore already printed the IGNORE line */ \
        } else if (UnityFailureCount > initial_failures) { \
            /* UnityFailHandler already printed the FAIL line */ \
        } else { \
            printf("TEST(%s):PASS\n", #test_func); \
        } \
    } while(0)

    RUN_TEST_WITH_PARSABLE_OUTPUT(test_is_string_empty_null_string);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_is_string_empty_empty_string);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_is_string_empty_non_empty_string);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_is_string_empty_string_with_spaces);

    RUN_TEST_WITH_PARSABLE_OUTPUT(test_reverse_string_null);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_reverse_string_empty);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_reverse_string_single_char);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_reverse_string_even_length);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_reverse_string_odd_length);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_reverse_string_palindrome);
    RUN_TEST_WITH_PARSABLE_OUTPUT(test_reverse_string_with_spaces);

    int overall_result = UNITY_END(); // Prints SUMMARY line and returns failure count

#if defined(__arm__) // Or other target macro
    qemu_exit(overall_result); // Signal QEMU to exit with the test result status
#endif

    return overall_result;
}
