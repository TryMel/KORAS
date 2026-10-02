package com.koras.koras_mobile.tools

import android.content.Context
import android.content.Intent
import android.net.Uri

/**
 * Section 35 — Outil de lancement d'applications et de navigation Maps.
 */
class AppTool(private val context: Context) {

    fun launchAppByName(appName: String, packageName: String? = null): Boolean {
        val pm = context.packageManager

        // If package name is provided directly
        if (!packageName.isNullOrBlank()) {
            val intent = pm.getLaunchIntentForPackage(packageName)
            if (intent != null) {
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
                context.startActivity(intent)
                return true
            }
        }

        // Search known applications
        val target = appName.lowercase().trim()
        val knownPackages = mapOf(
            "whatsapp" to "com.whatsapp",
            "youtube" to "com.google.android.youtube",
            "maps" to "com.google.android.apps.maps",
            "chrome" to "com.android.chrome",
            "calculatrice" to "com.google.android.calculator",
            "horloge" to "com.google.android.deskclock",
            "paramètres" to "com.android.settings",
            "settings" to "com.android.settings",
            "wave" to "com.wave.personal",
            "orange money" to "com.orange.orangemoney"
        )

        for ((name, pkg) in knownPackages) {
            if (target.contains(name)) {
                val intent = pm.getLaunchIntentForPackage(pkg)
                if (intent != null) {
                    intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
                    context.startActivity(intent)
                    return true
                }
            }
        }

        return false
    }

    fun openMaps(destination: String): Boolean {
        return try {
            val gmmIntentUri = Uri.parse("geo:0,0?q=" + Uri.encode(destination))
            val mapIntent = Intent(Intent.ACTION_VIEW, gmmIntentUri).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
                setPackage("com.google.android.apps.maps")
            }
            if (mapIntent.resolveActivity(context.packageManager) != null) {
                context.startActivity(mapIntent)
                true
            } else {
                // Browser fallback
                val webUri = Uri.parse("https://www.google.com/maps/search/?api=1&query=" + Uri.encode(destination))
                val webIntent = Intent(Intent.ACTION_VIEW, webUri).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK
                }
                context.startActivity(webIntent)
                true
            }
        } catch (e: Exception) {
            false
        }
    }

    fun openUrl(url: String): Boolean = try {
        val normalized = if (url.startsWith("http://") || url.startsWith("https://")) url else "https://$url"
        context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(normalized)).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        })
        true
    } catch (_: Exception) { false }

    fun searchWeb(query: String): Boolean = openUrl(
        "https://www.google.com/search?q=${Uri.encode(query)}"
    )
}
