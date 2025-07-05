#include "unity.h"
#include "utils/string_utils.h" // Path relative to CFLAGS -I../../src
#include <string.h> // For strcpy, strcmp
#include <stdint.h> // For intptr_t

// setUp and tearDown can be defined if needed
void setUp(void) {
    // No setup needed for these tests
}

void tearDown(void) {
    // No teardown needed
}

// Test cases for is_string_empty
void test_is_string_empty_null_string(void) {
    TEST_ASSERT_EQUAL_INT(1, is_string_empty(NULL)); // true is 1
}

void test_is_string_empty_empty_string(void) {
    TEST_ASSERT_EQUAL_INT(1, is_string_empty("")); // true is 1
}

void test_is_string_empty_non_empty_string(void) {
    TEST_ASSERT_EQUAL_INT(0, is_string_empty("hello")); // false is 0
}

void test_is_string_empty_string_with_spaces(void) {
    TEST_ASSERT_EQUAL_INT(0, is_string_empty("  ")); // false is 0
}

// Test cases for reverse_string
void test_reverse_string_null(void) {
    // Cast to intptr_t for comparing pointer with NULL as integer in TEST_ASSERT_EQUAL_INT
    TEST_ASSERT_EQUAL_INT((intptr_t)NULL, (intptr_t)reverse_string(NULL));
}

void test_reverse_string_empty(void) {
    char str[] = ""; // Mutable string
    reverse_string(str);
    TEST_ASSERT_EQUAL_INT(0, strcmp("", str));
}

void test_reverse_string_single_char(void) {
    char str[] = "a";
    reverse_string(str);
    TEST_ASSERT_EQUAL_INT(0, strcmp("a", str));
}

void test_reverse_string_even_length(void) {
    char str[] = "hello"; // Even number of chars before null terminator
    reverse_string(str);
    TEST_ASSERT_EQUAL_INT(0, strcmp("olleh", str));
}

void test_reverse_string_odd_length(void) {
    char str[] = "world!"; // Odd number of chars before null terminator
    reverse_string(str);
    TEST_ASSERT_EQUAL_INT(0, strcmp("!dlrow", str));
}

void test_reverse_string_palindrome(void) {
    char str[] = "madam";
    reverse_string(str);
    TEST_ASSERT_EQUAL_INT(0, strcmp("madam", str));
}

void test_reverse_string_with_spaces(void) {
    char str[] = "hello world";
    reverse_string(str);
    TEST_ASSERT_EQUAL_INT(0, strcmp("dlrow olleh", str));
}
