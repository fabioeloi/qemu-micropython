#include "unity.h"

// Forward declarations from test_data_processor.c
void test_initialize_sensor_system_success(void);
void test_initialize_sensor_system_init_fails(void);
void test_initialize_sensor_system_self_test_returns_false(void);
void test_initialize_sensor_system_self_test_bad_result_code(void);
void test_process_and_format_sensor_data_success(void);
void test_process_and_format_sensor_data_buffer_too_small(void);
void test_process_and_format_sensor_data_null_buffer(void);
void test_process_and_format_sensor_data_zero_buffer_size(void);

// setUp and tearDown are defined in test_data_processor.c
// These stubs are here if test_data_processor.c doesn't define them,
// to satisfy the placeholder Unity's UnityDefaultTestRun.
// However, best practice is for these to be in test_data_processor.c.
#ifndef TEST_SETUP_DEFINED_IN_TEST_FILE // Guard in case test file provides them
void setUp(void) {}
void tearDown(void) {}
#endif


// Using the MY_RUN_TEST macro logic for consistency with how string_utils runner was adapted
// for placeholder Unity and parseable output.
// With official Unity, this simplifies to just `RUN_TEST(test_func_name);`
#define MY_RUN_TEST(test_func_name) do { \
    /* These globals are part of the representative unity.h/unity.c */ \
    /* In full Unity, state is managed within the Unity struct more cleanly */ \
    Unity.CurrentTestName = #test_func_name; \
    Unity.CurrentTestLineNumber = (UNITY_LINE_TYPE)__LINE__; \
    Unity.CurrentTestFailed = 0; \
    Unity.CurrentTestIgnored = 0; \
    \
    unsigned int failures_before_run = Unity.TestFailures; \
    unsigned int ignores_before_run = Unity.TestIgnores; \
    \
    /* UnityDefaultTestRun is the placeholder's way to run setUp, test, tearDown */ \
    /* It also increments Unity.NumberOfTests */ \
    UnityDefaultTestRun(test_func_name, #test_func_name, (UNITY_LINE_TYPE)__LINE__); \
    \
    if (Unity.CurrentTestIgnored) { \
        /* IGNORE line printed by UnityIgnore in representative unity.c */ \
    } else if (Unity.CurrentTestFailed) { \
        /* FAIL line printed by UnityFailHandler in representative unity.c */ \
    } else if (Unity.TestFailures > failures_before_run) { \
        /* This case handles if an assert inside the test directly manipulated global Unity.TestFailures */ \
        /* but didn't set CurrentTestFailed, or if CurrentTestFailed was reset by mistake */ \
        /* It's a fallback for placeholder behavior. */ \
    } else { \
        printf("TEST(%s):PASS\n", #test_func_name); \
    } \
} while(0)


int main(void) {
    UNITY_BEGIN();

    MY_RUN_TEST(test_initialize_sensor_system_success);
    MY_RUN_TEST(test_initialize_sensor_system_init_fails);
    MY_RUN_TEST(test_initialize_sensor_system_self_test_returns_false);
    MY_RUN_TEST(test_initialize_sensor_system_self_test_bad_result_code);

    MY_RUN_TEST(test_process_and_format_sensor_data_success);
    MY_RUN_TEST(test_process_and_format_sensor_data_buffer_too_small);
    MY_RUN_TEST(test_process_and_format_sensor_data_null_buffer);
    MY_RUN_TEST(test_process_and_format_sensor_data_zero_buffer_size);

    return UNITY_END(); // Prints SUMMARY and returns failure count
}
