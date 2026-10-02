package com.koras.koras_mobile

import com.koras.koras_mobile.bridge.MethodChannelRegistry
import io.flutter.embedding.android.FlutterFragmentActivity
import io.flutter.embedding.engine.FlutterEngine

class MainActivity : FlutterFragmentActivity() {

    private var methodChannelRegistry: MethodChannelRegistry? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        methodChannelRegistry = MethodChannelRegistry(
            context = applicationContext,
            activity = this,
            messenger = flutterEngine.dartExecutor.binaryMessenger
        )
    }
}
