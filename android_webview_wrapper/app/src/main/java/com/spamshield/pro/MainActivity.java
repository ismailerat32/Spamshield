package com.spamshield.pro;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Build;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;

public class MainActivity extends Activity {
    private WebView webView;
    private FrameLayout root;
    private LinearLayout splashView;

    private static final String APP_URL = "https://spamshield-peld.onrender.com/login";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        root = new FrameLayout(this);
        setContentView(root);

        showSplash();

        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
            @Override
            public void run() {
                showWebView();
            }
        }, 2200);
    }

    private void showSplash() {
        splashView = new LinearLayout(this);
        splashView.setOrientation(LinearLayout.VERTICAL);
        splashView.setGravity(Gravity.CENTER);
        splashView.setPadding(42, 42, 42, 42);

        GradientDrawable bg = new GradientDrawable(
                GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{Color.rgb(2, 28, 17), Color.rgb(1, 10, 7)}
        );
        splashView.setBackground(bg);

        TextView shield = new TextView(this);
        shield.setText("🛡️");
        shield.setTextSize(64);
        shield.setGravity(Gravity.CENTER);

        TextView title = new TextView(this);
        title.setText("SpamShield PRO");
        title.setTextColor(Color.WHITE);
        title.setTextSize(32);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 20, 0, 8);

        TextView sub = new TextView(this);
        sub.setText("AI destekli SMS koruma");
        sub.setTextColor(Color.rgb(32, 240, 138));
        sub.setTextSize(17);
        sub.setTypeface(Typeface.DEFAULT_BOLD);
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, 0, 0, 18);

        TextView mini = new TextView(this);
        mini.setText("Güvenli giriş hazırlanıyor...");
        mini.setTextColor(Color.argb(170, 255, 255, 255));
        mini.setTextSize(13);
        mini.setGravity(Gravity.CENTER);

        splashView.addView(shield);
        splashView.addView(title);
        splashView.addView(sub);
        splashView.addView(mini);

        root.addView(
                splashView,
                new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                )
        );
    }

    private void showWebView() {
        webView = new WebView(this);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            settings.setSafeBrowsingEnabled(true);
        }

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();

                if (url.startsWith("https://spamshield-peld.onrender.com") || url.startsWith("https://eratshield.com")) {
                    return false;
                }

                return true;
            }
        });

        root.removeAllViews();
        root.addView(
                webView,
                new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                )
        );

        webView.loadUrl(APP_URL);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
