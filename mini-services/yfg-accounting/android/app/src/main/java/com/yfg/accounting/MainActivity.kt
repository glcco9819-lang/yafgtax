package com.yfg.accounting

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.os.Build
import android.webkit.CookieManager
import android.webkit.SafeBrowsingResponse
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.TextView
import android.widget.FrameLayout
import android.view.Gravity
import android.view.ViewGroup
import android.view.WindowInsets
import android.app.Activity

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var allowedOrigin: Uri

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        allowedOrigin = Uri.parse(BuildConfig.WEB_APP_URL)
        if (allowedOrigin.scheme != "https" || allowedOrigin.host.isNullOrBlank() || allowedOrigin.host == "replace-with-your-company-domain") {
            showMessage("نشانی امن سرور تنظیم نشده است. متغیر YFG_WEB_URL را هنگام ساخت APK روی نشانی HTTPS دفتر تنظیم کنید.")
            return
        }

        webView = WebView(this)
        webView.layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        if (Build.VERSION.SDK_INT >= 30) {
            webView.setOnApplyWindowInsetsListener { view, insets ->
                val bars = insets.getInsets(WindowInsets.Type.systemBars())
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
                insets
            }
        }
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW
            javaScriptCanOpenWindowsAutomatically = false
            setSupportMultipleWindows(false)
            safeBrowsingEnabled = true
        }
        CookieManager.getInstance().setAcceptCookie(true)
        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val uri = request.url
                if (isAllowed(uri)) return false
                if (uri.scheme == "https" || uri.scheme == "http") {
                    runCatching { startActivity(Intent(Intent.ACTION_VIEW, uri)) }
                }
                return true
            }

            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: android.webkit.WebResourceError) {
                if (request.isForMainFrame) showMessage("اتصال به سرور برقرار نشد. اتصال اینترنت یا VPN دفتر را بررسی و دوباره تلاش کنید.\n\n${error.description}")
            }

            override fun onSafeBrowsingHit(view: WebView, request: WebResourceRequest, threatType: Int, callback: SafeBrowsingResponse) {
                callback.backToSafety(true)
            }
        }
        setContentView(webView)
        if (savedInstanceState == null) webView.loadUrl(BuildConfig.WEB_APP_URL) else webView.restoreState(savedInstanceState)
    }

    private fun isAllowed(uri: Uri): Boolean {
        val requestedPort = if (uri.port == -1) 443 else uri.port
        val configuredPort = if (allowedOrigin.port == -1) 443 else allowedOrigin.port
        return uri.scheme == "https" && uri.host.equals(allowedOrigin.host, ignoreCase = true) && requestedPort == configuredPort
    }

    private fun showMessage(message: String) {
        val text = TextView(this).apply {
            this.text = message
            textSize = 17f
            gravity = Gravity.CENTER
            setPadding(36, 36, 36, 36)
            setTextColor(android.graphics.Color.rgb(28, 50, 62))
        }
        setContentView(FrameLayout(this).apply { addView(text, FrameLayout.LayoutParams(-1, -1)) })
    }

    override fun onSaveInstanceState(outState: Bundle) {
        if (::webView.isInitialized) webView.saveState(outState)
        super.onSaveInstanceState(outState)
    }

    @Deprecated("Deprecated in Android API; retained for broad device compatibility")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
