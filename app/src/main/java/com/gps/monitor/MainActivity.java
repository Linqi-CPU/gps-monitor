package com.gps.monitor;

import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.os.Bundle;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.Manifest;
import android.content.pm.PackageManager;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity {
    private static final int LOCATION_PERMISSION_REQUEST = 1;
    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webview);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setGeolocationEnabled(true);
        settings.setGeolocationDatabasePath(getApplicationContext().getFilesDir().getPath());
        settings.setDatabaseEnabled(true);
        settings.setDatabasePath(getApplicationContext().getFilesDir().getPath());

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                // Auto-grant geolocation permission for the GPS monitor URL
                if (origin.contains("10.102.105.251") || origin.contains("localhost")) {
                    callback.invoke(origin, true, false);
                } else {
                    new AlertDialog.Builder(MainActivity.this)
                            .setTitle("位置权限")
                            .setMessage("允许 " + origin + " 获取您的位置信息吗？")
                            .setPositiveButton("允许", (dialog, which) -> callback.invoke(origin, true, false))
                            .setNegativeButton("拒绝", (dialog, which) -> callback.invoke(origin, false, false))
                            .show();
                }
            }
        });

        // Request location permission at runtime
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION},
                    LOCATION_PERMISSION_REQUEST);
        }

        webView.loadUrl("http://10.102.105.251:8080/gps_monitor.html");
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == LOCATION_PERMISSION_REQUEST) {
            // Permission result handled by system, WebView will use permissions
        }
    }
}
