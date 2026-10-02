package com.koras.koras_mobile.tools

import android.content.Context
import android.content.Intent
import android.net.Uri

/**
 * Section 35 — N1 : Outil d'appel téléphonique réel Android.
 */
class PhoneTool(private val context: Context) {

    fun makeCall(phoneNumber: String): Boolean {
        return try {
            val cleanNumber = phoneNumber.replace(Regex("[^0-9+]"), "")
            if (cleanNumber.isBlank()) return false
            val intent = Intent(Intent.ACTION_CALL).apply {
                data = Uri.parse("tel:$cleanNumber")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
            true
        } catch (e: Exception) {
            // Fallback to DIAL if CALL_PHONE permission not granted
            try {
                val dialIntent = Intent(Intent.ACTION_DIAL).apply {
                    data = Uri.parse("tel:$phoneNumber")
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                context.startActivity(dialIntent)
                true
            } catch (ex: Exception) {
                false
            }
        }
    }
}
