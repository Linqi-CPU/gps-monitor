package com.gps.monitor;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.AlertDialog;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class MainActivity extends AppCompatActivity implements LocationListener {

    private static final int LOCATION_PERMISSION_REQUEST = 100;
    private LocationManager locationManager;
    private TextView statusText;
    private TextView latText, lonText, accText, altText, spdText;
    private Button startBtn, stopBtn, clearBtn;
    private LinearLayout historyContainer;
    private boolean isTracking = false;
    private List<String> historyList = new ArrayList<>();
    private Handler handler = new Handler(Looper.getMainLooper());

    @SuppressLint("MissingPermission")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // 主布局
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#1a1a2e"));
        root.setPadding(20, 20, 20, 20);

        // 标题
        TextView title = new TextView(this);
        title.setText("📍 GPS 定位监控");
        title.setTextSize(24);
        title.setTextColor(Color.WHITE);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, 20);
        root.addView(title);

        // 状态栏
        statusText = new TextView(this);
        statusText.setText("● 未定位");
        statusText.setTextSize(16);
        statusText.setTextColor(Color.RED);
        statusText.setPadding(0, 0, 0, 20);
        root.addView(statusText);

        // 数据卡片
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackgroundColor(Color.parseColor("#16213e"));
        card.setPadding(20, 20, 20, 20);
        LinearLayout.LayoutParams cardParams = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 
                LinearLayout.LayoutParams.WRAP_CONTENT);
        cardParams.setMargins(0, 0, 0, 20);
        card.setLayoutParams(cardParams);

        // 纬度
        latText = makeField("纬度 (Latitude)", "39.904200°");
        card.addView(latText);

        // 经度
        lonText = makeField("经度 (Longitude)", "116.407400°");
        card.addView(lonText);

        // 精度
        accText = makeField("精度 (Accuracy)", "--");
        card.addView(accText);

        // 海拔
        altText = makeField("海拔 (Altitude)", "--");
        card.addView(altText);

        // 速度
        spdText = makeField("速度 (Speed)", "--");
        card.addView(spdText);

        root.addView(card);

        // 按钮区
        LinearLayout btnRow = new LinearLayout(this);
        btnRow.setOrientation(LinearLayout.HORIZONTAL);
        int spacing = 10;

        startBtn = makeButton("🚀 开始定位", Color.parseColor("#667eea"));
        stopBtn = makeButton("⏹️ 停止", Color.parseColor("#ff6b6b"));
        clearBtn = makeButton("🗑️ 清空", Color.parseColor("#444"));

        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
        p.rightMargin = spacing;
        btnRow.addView(startBtn, p);
        btnRow.addView(stopBtn, p);
        btnRow.addView(clearBtn);

        startBtn.setOnClickListener(v -> startTracking());
        stopBtn.setOnClickListener(v -> stopTracking());
        clearBtn.setOnClickListener(v -> clearHistory());

        root.addView(btnRow);

        // 历史记录标题
        TextView historyTitle = new TextView(this);
        historyTitle.setText("📊 定位历史");
        historyTitle.setTextSize(18);
        historyTitle.setTextColor(Color.WHITE);
        historyTitle.setPadding(0, 20, 0, 10);
        root.addView(historyTitle);

        // 历史记录列表
        historyContainer = new LinearLayout(this);
        historyContainer.setOrientation(LinearLayout.VERTICAL);
        root.addView(historyContainer);

        setContentView(root);

        locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
    }

    private LinearLayout makeField(String label, String value) {
        LinearLayout field = new LinearLayout(this);
        field.setOrientation(LinearLayout.VERTICAL);
        
        TextView lbl = new TextView(this);
        lbl.setText(label);
        lbl.setTextSize(12);
        lbl.setTextColor(Color.GRAY);
        
        TextView val = new TextView(this);
        val.setText(value);
        val.setTextSize(20);
        val.setTextColor(Color.CYAN);
        val.setTypeface(null, android.graphics.Typeface.BOLD);
        
        field.addView(lbl);
        field.addView(val);
        return field;
    }

    private Button makeButton(String text, int color) {
        Button btn = new Button(this);
        btn.setText(text);
        btn.setTextSize(16);
        btn.setTextColor(Color.WHITE);
        btn.setBackgroundColor(color);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                0, 
                LinearLayout.LayoutParams.WRAP_CONTENT, 
                1);
        btn.setLayoutParams(params);
        return btn;
    }

    @SuppressLint("MissingPermission")
    private void startTracking() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) 
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION, 
                                Manifest.permission.ACCESS_COARSE_LOCATION},
                    LOCATION_PERMISSION_REQUEST);
            return;
        }

        isTracking = true;
        startBtn.setEnabled(false);
        stopBtn.setEnabled(true);
        statusText.setText("● 正在定位...");
        statusText.setTextColor(Color.YELLOW);

        locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000, 0, this);
        locationManager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 1000, 0, this);
    }

    private void stopTracking() {
        isTracking = false;
        startBtn.setEnabled(true);
        stopBtn.setEnabled(false);
        statusText.setText("● 已停止");
        statusText.setTextColor(Color.RED);
        
        if (locationManager != null) {
            locationManager.removeUpdates(this);
        }
    }

    private void clearHistory() {
        historyList.clear();
        historyContainer.removeAllViews();
        Toast.makeText(this, "已清空历史", Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onLocationChanged(@NonNull Location location) {
        if (!isTracking) return;

        double lat = location.getLatitude();
        double lon = location.getLongitude();
        float acc = location.getAccuracy();
        double alt = location.getAltitude();
        float spd = location.getSpeed();

        // 更新 UI
        latText.getChildAt(1).setText(String.format("%.6f°", lat));
        lonText.getChildAt(1).setText(String.format("%.6f°", lon));
        accText.getChildAt(1).setText(String.format("%.1f 米", acc));
        altText.getChildAt(1).setText(String.format("%.1f 米", alt));
        spdText.getChildAt(1).setText(String.format("%.1f km/h", spd * 3.6));

        statusText.setText("● GPS 定位成功");
        statusText.setTextColor(Color.GREEN);

        // 添加到历史
        String time = new SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(new Date());
        String record = String.format("%s  %.6f, %.6f", time, lat, lon);
        historyList.add(0, record);
        if (historyList.size() > 50) historyList.remove(historyList.size() - 1);

        // 更新历史显示
        handler.post(() -> {
            historyContainer.removeAllViews();
            for (String line : historyList) {
                TextView tv = new TextView(this);
                tv.setText(line);
                tv.setTextSize(12);
                tv.setTextColor(Color.LTGRAY);
                tv.setPadding(0, 5, 0, 5);
                historyContainer.addView(tv);
            }
        });
    }

    @Override
    public void onProviderEnabled(@NonNull String provider) {
        statusText.setText("● 定位可用: " + provider);
    }

    @Override
    public void onProviderDisabled(@NonNull String provider) {
        statusText.setText("● 定位不可用: " + provider);
    }

    @Override
    public void onStatusChanged(String provider, int status, Bundle extras) {}

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == LOCATION_PERMISSION_REQUEST) {
            boolean granted = true;
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    granted = false;
                    break;
                }
            }
            if (granted) {
                startTracking();
            } else {
                Toast.makeText(this, "需要位置权限才能使用 GPS", Toast.LENGTH_LONG).show();
            }
        }
    }
}
