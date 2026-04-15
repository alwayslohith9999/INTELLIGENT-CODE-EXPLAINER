"""
GCC diagnostic categories, canned explanations, and synthetic training lines.
Used to train a local classifier (see train_explainer.py) and at inference time.
"""
from __future__ import annotations

# category_id -> fields matching the API schema for one issue
CATEGORY_EXPLANATIONS: dict[str, dict[str, str]] = {
    "generic": {
        "plain_explanation": "GCC reported a problem at this location.",
        "likely_cause": "The message above describes what the compiler objected to.",
        "suggested_fix": "Read the exact diagnostic text, compare with nearby source lines, and adjust types, syntax, or declarations accordingly.",
    },
    "implicit_function_declaration": {
        "plain_explanation": "You called a function before the compiler knew its prototype.",
        "likely_cause": "Missing #include (e.g. <stdio.h>) or a forward declaration before the call.",
        "suggested_fix": "Add the correct header, e.g. #include <stdio.h> for printf/scanf, or declare the function before use.",
    },
    "undefined_reference": {
        "plain_explanation": "The linker could not find a symbol (function or variable) used by your program.",
        "likely_cause": "Wrong function name, missing source file in the link step, or missing -l library flag.",
        "suggested_fix": "Fix the name, link the .c file that defines the symbol, or add the right library (e.g. -lm for math).",
    },
    "expected_semicolon": {
        "plain_explanation": "A statement ended where GCC still expected more tokens—often a missing semicolon.",
        "likely_cause": "Forgot ; after an expression statement, struct member declaration, or return.",
        "suggested_fix": "Insert ; at the end of the previous full statement on or above the indicated line.",
    },
    "expected_brace_paren": {
        "plain_explanation": "Brackets or parentheses do not balance at this point in the source.",
        "likely_cause": "Extra/missing { } ( ) [ ] from editing or copy-paste.",
        "suggested_fix": "Match each opening delimiter with a closing one; use editor bracket-matching to find the mismatch.",
    },
    "undeclared_variable": {
        "plain_explanation": "A name was used that is not declared in this scope.",
        "likely_cause": "Typo, wrong scope, or missing declaration / parameter.",
        "suggested_fix": "Declare the variable before use, fix the spelling, or pass it as a parameter.",
    },
    "conflicting_types": {
        "plain_explanation": "The same identifier was given incompatible types in different places.",
        "likely_cause": "Mismatched declaration vs definition, or duplicate declarations with different types.",
        "suggested_fix": "Make all declarations and the single definition use exactly the same type.",
    },
    "invalid_initializer": {
        "plain_explanation": "An initializer does not match what C allows for that object.",
        "likely_cause": "Wrong braces for arrays/structs, or type mismatch in assignment-style init.",
        "suggested_fix": "Follow C rules for initializing that kind of object; check array vs scalar syntax.",
    },
    "pointer_arithmetic": {
        "plain_explanation": "Pointer arithmetic or conversion here is not allowed.",
        "likely_cause": "Arithmetic on void*, wrong types in pointer +/- int, or invalid cast.",
        "suggested_fix": "Use a concrete pointer type; ensure only pointers to compatible array elements are combined.",
    },
    "incompatible_pointer": {
        "plain_explanation": "Pointers of incompatible types are mixed without a proper cast (if any is allowed).",
        "likely_cause": "Assigning int* to char* (or vice versa) without an explicit cast where you really need it.",
        "suggested_fix": "Use the correct pointer type end-to-end, or refactor so casts are not needed.",
    },
    "return_type_mismatch": {
        "plain_explanation": "What you return does not match the function's declared return type.",
        "likely_cause": "Missing return, wrong expression type, or void function returning a value.",
        "suggested_fix": "Change the return expression or the function's return type so they agree with a single consistent design.",
    },
    "wrong_main_signature": {
        "plain_explanation": "main's parameters or return type do not match the standard forms.",
        "likely_cause": "Non-standard main declaration for a hosted environment.",
        "suggested_fix": "Use int main(void) or int main(int argc, char *argv[]) and return an int status.",
    },
    "array_bounds": {
        "plain_explanation": "Array access may be out of bounds (especially with warnings enabled).",
        "likely_cause": "Loop bound off-by-one or wrong index expression.",
        "suggested_fix": "Ensure indices are in [0, N-1] for size N; fix loop conditions.",
    },
    "format_string": {
        "plain_explanation": "printf/scanf format string does not match the argument types or count.",
        "likely_cause": "Wrong % specifier, too few/many arguments, or passing wrong type.",
        "suggested_fix": "Match each % to the next argument's type (e.g. %d for int, %s for char*).",
    },
    "unreachable_code": {
        "plain_explanation": "Code can never execute (often after return or inside a branch that always exits).",
        "likely_cause": "Logic error or leftover statements after return.",
        "suggested_fix": "Remove dead code or restructure control flow so the intended path can run.",
    },
    "unused_variable": {
        "plain_explanation": "A variable is never used (warning).",
        "likely_cause": "Leftover from refactoring or a placeholder you forgot to use.",
        "suggested_fix": "Remove the variable or use it; prefix with (void)var; or mark intentionally unused if your style allows.",
    },
    "implicit_int": {
        "plain_explanation": "Old-style implicit int is not allowed in C99/C11.",
        "likely_cause": "Function or variable declared without a type (legacy style).",
        "suggested_fix": "Add explicit types everywhere (e.g. int main(void)).",
    },
    "division_by_zero": {
        "plain_explanation": "Compile-time or constant evaluation detected division by zero.",
        "likely_cause": "Literal 0 in the denominator or a macro expanding to 0.",
        "suggested_fix": "Guard the divisor or use a nonzero constant.",
    },
    "case_label": {
        "plain_explanation": "A case or default label is misplaced relative to switch syntax.",
        "likely_cause": "case outside switch, duplicate case values, or missing break where logic requires it.",
        "suggested_fix": "Put cases only inside a switch block; ensure each case value is unique.",
    },
    "struct_incomplete": {
        "plain_explanation": "A struct type is incomplete at the point of use.",
        "likely_cause": "Using struct before its full definition, or wrong struct tag.",
        "suggested_fix": "Define the struct before use or include the header that defines it.",
    },
    "redefinition": {
        "plain_explanation": "The same identifier is defined more than once in the same scope.",
        "likely_cause": "Duplicate variable/function definitions or duplicate #include without include guards.",
        "suggested_fix": "Remove the duplicate, use static/file scope correctly, or add header guards / #pragma once.",
    },
    "storage_class": {
        "plain_explanation": "Invalid combination of storage-class specifiers or linkage.",
        "likely_cause": "Conflicting static/extern, or illegal placement.",
        "suggested_fix": "Use one consistent linkage rule per identifier across translation units.",
    },
    "const_violation": {
        "plain_explanation": "A const-qualified object would be modified illegally.",
        "likely_cause": "Assigning through a const pointer or discarding const incorrectly.",
        "suggested_fix": "Remove const only if mutation is intended, or avoid writing through const pointers.",
    },
    "sizeof_invalid": {
        "plain_explanation": "sizeof is applied to something invalid or incomplete.",
        "likely_cause": "sizeof on incomplete type, function, or void.",
        "suggested_fix": "Apply sizeof only to complete object types; ensure includes define the type fully.",
    },
    "void_value": {
        "plain_explanation": "A void expression is used where a value is required.",
        "likely_cause": "Using the result of a void function in an expression.",
        "suggested_fix": "Do not use the return value of void functions; call them as standalone statements.",
    },
    "assignment_discards_qualifiers": {
        "plain_explanation": "Assignment drops qualifiers like const in a way that is not allowed.",
        "likely_cause": "Assigning const T* to T* without cast (unsafe).",
        "suggested_fix": "Keep const correctness end-to-end or use an explicit safe copy.",
    },
    "macro_redefined": {
        "plain_explanation": "A macro was defined differently on a second #define.",
        "likely_cause": "Conflicting headers or duplicate definitions with different values.",
        "suggested_fix": "Use include order fixes, #undef before redefining, or rename one macro.",
    },
    "include_file_not_found": {
        "plain_explanation": "The compiler could not open a #included file.",
        "likely_cause": "Wrong path, typo in filename, or missing dev package.",
        "suggested_fix": "Fix the #include name; add -I paths or install the SDK that provides the header.",
    },
    "linker_collect2": {
        "plain_explanation": "The linker (often invoked as collect2) reported a failure.",
        "likely_cause": "Unresolved symbols, duplicate definitions, or platform-specific link issues.",
        "suggested_fix": "Read the first undefined reference or duplicate symbol message and fix sources or link flags.",
    },
}

# (training text fragment, category_id) — synthetic data for the local classifier
TRAINING_PAIRS: list[tuple[str, str]] = [
    ("implicit declaration of function 'printf'", "implicit_function_declaration"),
    ("implicit declaration of function 'malloc'", "implicit_function_declaration"),
    ("implicit declaration of function 'strlen'", "implicit_function_declaration"),
    ("implicit declaration of function 'puts'", "implicit_function_declaration"),
    ("implicit declaration of function 'scanf'", "implicit_function_declaration"),
    ("warning: implicit declaration of function", "implicit_function_declaration"),
    ("undefined reference to `printf'", "undefined_reference"),
    ("undefined reference to `main'", "undefined_reference"),
    ("undefined reference to `sqrt'", "undefined_reference"),
    ("undefined reference to ", "undefined_reference"),
    ("expected ';' before", "expected_semicolon"),
    ("expected ';' or", "expected_semicolon"),
    ("expected declaration or statement at end of input", "expected_brace_paren"),
    ("expected '}' at", "expected_brace_paren"),
    ("expected ')' before", "expected_brace_paren"),
    ("expected '(' after", "expected_brace_paren"),
    ("undeclared (first use in this function)", "undeclared_variable"),
    ("undeclared identifier", "undeclared_variable"),
    ("'x' undeclared", "undeclared_variable"),
    ("conflicting types for", "conflicting_types"),
    ("conflicting types for 'foo'", "conflicting_types"),
    ("invalid initializer", "invalid_initializer"),
    ("invalid array initializer", "invalid_initializer"),
    ("invalid operands to binary", "pointer_arithmetic"),
    ("invalid use of void expression", "void_value"),
    ("incompatible types when assigning", "incompatible_pointer"),
    ("incompatible pointer type", "incompatible_pointer"),
    ("initialization from incompatible pointer type", "incompatible_pointer"),
    ("return type of 'main' is not 'int'", "wrong_main_signature"),
    ("first argument of 'main' should be 'int'", "wrong_main_signature"),
    ("return type mismatch", "return_type_mismatch"),
    ("format '%d' expects argument of type 'int'", "format_string"),
    ("format '%s' expects argument of type", "format_string"),
    ("too many arguments for format", "format_string"),
    ("missing terminating ' character", "generic"),
    ("array subscript is above array bounds", "array_bounds"),
    ("array subscript below zero", "array_bounds"),
    ("unreachable code", "unreachable_code"),
    ("unused variable", "unused_variable"),
    ("unused parameter", "unused_variable"),
    ("type defaults to 'int' in declaration", "implicit_int"),
    ("division by zero", "division_by_zero"),
    ("case label not within a switch statement", "case_label"),
    ("duplicate case value", "case_label"),
    ("dereferencing pointer to incomplete type", "struct_incomplete"),
    ("storage size of 's' isn't known", "struct_incomplete"),
    ("redefinition of", "redefinition"),
    ("conflicting types for 'struct", "conflicting_types"),
    ("invalid storage class for function", "storage_class"),
    ("assignment discards 'const' qualifier", "assignment_discards_qualifiers"),
    ("invalid application of 'sizeof' to void type", "sizeof_invalid"),
    ("void value not ignored as it ought to be", "void_value"),
    ("macro redefined", "macro_redefined"),
    ("No such file or directory", "include_file_not_found"),
    ("fatal error: stdio.h: No such file", "include_file_not_found"),
    ("collect2: error:", "linker_collect2"),
    ("ld returned 1 exit status", "linker_collect2"),
]

# Augment training data with small variations (helps TF-IDF)
def expanded_training_pairs() -> list[tuple[str, str]]:
    out = list(TRAINING_PAIRS)
    for text, cat in TRAINING_PAIRS:
        out.append((text.lower(), cat))
        out.append((text.upper(), cat))
    return out
