package com.koras.koras_mobile.tools

import android.content.Context
import android.content.Intent
import android.provider.CalendarContract

/** Opens Android Calendar with the requested item pre-filled. Android owns the final save. */
class CalendarTool(private val context: Context) {
    fun createReminder(title: String): Boolean = openInsert(title, "Rappel KORAS")

    fun createEvent(title: String, description: String? = null): Boolean = openInsert(title, description)

    private fun openInsert(title: String, description: String?): Boolean = try {
        context.startActivity(Intent(Intent.ACTION_INSERT).apply {
            data = CalendarContract.Events.CONTENT_URI
            putExtra(CalendarContract.Events.TITLE, title)
            putExtra(CalendarContract.Events.DESCRIPTION, description)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        })
        true
    } catch (_: Exception) { false }
}
