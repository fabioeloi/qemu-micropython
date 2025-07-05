#include "unity.h"

// Forward declarations of test functions from test_string_utils.c
// Ensure these match the function signatures in test_string_utils.c
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

// setUp and tearDown are called by Unity's default runner logic (via RUN_TEST macro)
// If your test_string_utils.c defines them, they will be used.
// If not, these empty ones will be used (or linker might complain if not defined anywhere and RUN_TEST expects them).
// The placeholder unity.c's UnityDefaultTestRun calls them, so they must be defined.
void setUp(void) {
    // No specific setup for this test suite
}

void tearDown(void) {
    // No specific teardown for this test suite
}

int main(void) {
    UNITY_BEGIN(); // Must be called first

    RUN_TEST(test_is_string_empty_null_string, __LINE__);
    RUN_TEST(test_is_string_empty_empty_string, __LINE__);
    RUN_TEST(test_is_string_empty_non_empty_string, __LINE__);
    RUN_TEST(test_is_string_empty_string_with_spaces, __LINE__);

    RUN_TEST(test_reverse_string_null, __LINE__);
    RUN_TEST(test_reverse_string_empty, __LINE__);
    RUN_TEST(test_reverse_string_single_char, __LINE__);
    RUN_TEST(test_reverse_string_even_length, __LINE__);
    RUN_TEST(test_reverse_string_odd_length, __LINE__);
    RUN_TEST(test_reverse_string_palindrome, __LINE__);
    RUN_TEST(test_reverse_string_with_spaces, __LINE__);

    return UNITY_END(); // Returns 0 on pass, non-zero on fail
}
