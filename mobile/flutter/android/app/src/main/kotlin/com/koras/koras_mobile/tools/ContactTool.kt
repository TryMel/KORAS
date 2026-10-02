package com.koras.koras_mobile.tools

import android.content.Context
import android.provider.ContactsContract

/** Resolves a contact locally. No address book data leaves the device. */
class ContactTool(private val context: Context) {
    fun search(query: String, limit: Int = 10): List<Map<String, String>> {
        if (query.isBlank()) return emptyList()
        val projection = arrayOf(
            ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
            ContactsContract.CommonDataKinds.Phone.NUMBER,
        )
        return try {
            context.contentResolver.query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
                projection,
                "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?",
                arrayOf("%${query.trim()}%"),
                "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} ASC"
            )?.use { cursor ->
                buildList {
                    while (cursor.moveToNext() && size < limit) add(mapOf(
                        "name" to cursor.getString(0), "phone_number" to cursor.getString(1)
                    ))
                }
            } ?: emptyList()
        } catch (_: SecurityException) { emptyList() }
    }

    fun findPhoneNumber(name: String): String? {
        if (name.isBlank()) return null
        val projection = arrayOf(ContactsContract.CommonDataKinds.Phone.NUMBER)
        val selection = "${ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?"
        val args = arrayOf("%${name.trim()}%")
        return try {
            context.contentResolver.query(
                ContactsContract.CommonDataKinds.Phone.CONTENT_URI, projection, selection, args,
                "${ContactsContract.CommonDataKinds.Phone.IS_PRIMARY} DESC"
            )?.use { cursor ->
                if (cursor.moveToFirst()) cursor.getString(0) else null
            }
        } catch (_: SecurityException) {
            null
        }
    }
}
