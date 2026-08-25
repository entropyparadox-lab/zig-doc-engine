#ifndef DOC_ENGINE_H
#define DOC_ENGINE_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void* DocEngineHandle;

/**
 * Open a DocEngine SQLite FTS5 database instance.
 * @param db_path Path to the SQLite database file.
 * @param read_only Open in read-only mode if true.
 * @return Handle pointer, or NULL on error.
 */
DocEngineHandle doc_engine_open(const char* db_path, bool read_only);

/**
 * Close and release the DocEngine instance.
 * @param handle Valid DocEngineHandle.
 */
void doc_engine_close(DocEngineHandle handle);

/**
 * Search the documentation corpus and return a formatted JSON string.
 * @param handle Valid DocEngineHandle.
 * @param query Search query string.
 * @param lib_filter Optional library ID filter (can be NULL or empty).
 * @param limit Maximum results count.
 * @return Heap-allocated JSON string (must be freed with doc_engine_free_string), or NULL on error.
 */
char* doc_engine_search_json(DocEngineHandle handle, const char* query, const char* lib_filter, size_t limit);

/**
 * Search the documentation corpus with explicit version filtering.
 * @param handle Valid DocEngineHandle.
 * @param query Search query string.
 * @param lib_filter Optional library ID filter.
 * @param ver_filter Optional version filter (e.g. "0.7", "18", "v3").
 * @param limit Maximum results count.
 * @return Heap-allocated JSON string (must be freed with doc_engine_free_string), or NULL on error.
 */
char* doc_engine_search_json_ver(DocEngineHandle handle, const char* query, const char* lib_filter, const char* ver_filter, size_t limit);

/**
 * Free a string allocated by doc_engine_search_json.
 * @param str Pointer to string.
 */
void doc_engine_free_string(char* str);

#ifdef __cplusplus
}
#endif

#endif // DOC_ENGINE_H
