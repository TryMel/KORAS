package com.koras.koras_mobile.accessibility

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.Rect
import android.os.Build
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import java.lang.ref.WeakReference

/**
 * Section 21 & 22 — Service d'accessibilité natif KORAS.
 * Destiné à l'assistance, la lecture d'écran sémantique et l'action contrôlée.
 */
class KorasAccessibilityService : AccessibilityService() {

    companion object {
        var instance: WeakReference<KorasAccessibilityService>? = null

        fun isRunning(): Boolean = instance?.get() != null
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = WeakReference(this)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Observes state changes without logging private data (Section 22)
    }

    override fun onInterrupt() {
        // Handle interruption
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
    }

    /**
     * Lit la hiérarchie des fenêtres et normalise les éléments interactifs.
     */
    fun readNormalizedScreen(): Map<String, Any> {
        val rootNode = rootInActiveWindow ?: return mapOf("screen" to "empty", "elements" to emptyList<Map<String, Any>>())
        val elements = mutableListOf<Map<String, Any>>()
        traverseNode(rootNode, elements)
        return mapOf(
            "screen" to (rootNode.packageName?.toString() ?: "unknown"),
            "elements" to elements
        )
    }

    private fun traverseNode(node: AccessibilityNodeInfo?, list: MutableList<Map<String, Any>>) {
        if (node == null) return

        val text = node.text?.toString() ?: node.contentDescription?.toString()
        if (!text.isNullOrBlank() || node.isClickable) {
            val rect = Rect()
            node.getBoundsInScreen(rect)

            list.add(
                mapOf(
                    "type" to (node.className?.toString() ?: "view"),
                    "label" to (text ?: ""),
                    "clickable" to node.isClickable,
                    "bounds" to mapOf(
                        "left" to rect.left,
                        "top" to rect.top,
                        "right" to rect.right,
                        "bottom" to rect.bottom
                    )
                )
            )
        }

        for (i in 0 until node.childCount) {
            traverseNode(node.getChild(i), list)
        }
    }

    /**
     * Effectue un clic sur un élément précis par coordonnées
     */
    fun performClickAt(x: Float, y: Float): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            val path = Path().apply { moveTo(x, y) }
            val stroke = GestureDescription.StrokeDescription(path, 0, 100)
            val gesture = GestureDescription.Builder().addStroke(stroke).build()
            return dispatchGesture(gesture, null, null)
        }
        return false
    }

    /** Clicks an element only when its visible accessibility label matches. */
    fun performClickByLabel(label: String): Boolean {
        val root = rootInActiveWindow ?: return false
        return findAndClick(root, label.trim())
    }

    private fun findAndClick(node: AccessibilityNodeInfo?, label: String): Boolean {
        if (node == null) return false
        val nodeLabel = node.text?.toString() ?: node.contentDescription?.toString() ?: ""
        if (nodeLabel.equals(label, ignoreCase = true) && node.isClickable) {
            return node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        }
        for (index in 0 until node.childCount) if (findAndClick(node.getChild(index), label)) return true
        return false
    }
}
