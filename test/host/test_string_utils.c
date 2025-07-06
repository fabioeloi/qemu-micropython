#include "unity.h"
#include "utils/string_utils.h" // Path relative to CFLAGS -I../../src
#include <string.h> // For strcpy for mutable test strings if needed
#include <stdint.h> // For intptr_t (though not strictly needed with TEST_ASSERT_NULL)

// setUp and tearDown can be defined if needed
void setUp(void) {
    // No setup needed for these tests
}

void tearDown(void) {
    // No teardown needed
}

// Test cases for is_string_empty
void test_is_string_empty_null_string(void) {
    TEST_ASSERT_TRUE(is_string_empty(NULL));
}

void test_is_string_empty_empty_string(void) {
    TEST_ASSERT_TRUE(is_string_empty(""));
}

void test_is_string_empty_non_empty_string(void) {
    TEST_ASSERT_FALSE(is_string_empty("hello"));
}

void test_is_string_empty_string_with_spaces(void) {
    TEST_ASSERT_FALSE(is_string_empty("  "));
}

// Test cases for reverse_string
void test_reverse_string_null(void) {
    TEST_ASSERT_NULL(reverse_string(NULL));
}

void test_reverse_string_empty(void) {
    char str[] = ""; // Mutable string
    reverse_string(str);
    TEST_ASSERT_EQUAL_STRING("", str);
}

void test_reverse_string_single_char(void) {
    char str[] = "a";
    reverse_string(str);
    TEST_ASSERT_EQUAL_STRING("a", str);
}

void test_reverse_string_even_length(void) {
    char str[] = "hello";
    reverse_string(str);
    TEST_ASSERT_EQUAL_STRING("olleh", str);
}

void test_reverse_string_odd_length(void) {
    char str[] = "world!";
    reverse_string(str);
    TEST_ASSERT_EQUAL_STRING("!dlrow", str);
}

void test_reverse_string_palindrome(void) {
    char str[] = "madam";
    reverse_string(str);
    TEST_ASSERT_EQUAL_STRING("madam", str);
}

void test_reverse_string_with_spaces(void) {
    char str[] = "hello world";
    reverse_string(str);
    TEST_ASSERT_EQUAL_STRING("dlrow olleh", str);
}
