package com.gps.monitor;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.Context;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Gravity;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import java.io.IOException;
import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class MainActivity extends AppCompatActivity implements LocationListener {

    private static final String TAG = "GPSMonitor";
    private static final int LOCATION_PERMISSION_REQUEST = 100;
    private LocationManager locationManager;
    private TextView statusText;
    private TextView latValue, lonValue, accValue, altValue, spdValue;
    private TextView provinceText;  // 省份显示
    private Button startBtn, stopBtn, clearBtn;
    private LinearLayout historyContainer;
    private ImageView mapView;  // 地图
    private boolean isTracking = false;
    private List<String> historyList = new ArrayList<>();
    private Handler handler = new Handler(Looper.getMainLooper());
    private ProvinceMap provinceMap;
    private ProvinceInferencer inferencer;
    private TextView directionText; // 方向提示

    @SuppressLint("MissingPermission")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.d(TAG, "onCreate started");
        
        try {
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

            // 状态
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
            LinearLayout latField = makeField("纬度 (Latitude)", "--");
            latValue = (TextView) latField.getChildAt(1);
            card.addView(latField);

            // 经度
            LinearLayout lonField = makeField("经度 (Longitude)", "--");
            lonValue = (TextView) lonField.getChildAt(1);
            card.addView(lonField);

            // 精度
            LinearLayout accField = makeField("精度 (Accuracy)", "--");
            accValue = (TextView) accField.getChildAt(1);
            card.addView(accField);

            // 海拔
            LinearLayout altField = makeField("海拔 (Altitude)", "--");
            altValue = (TextView) altField.getChildAt(1);
            card.addView(altField);

            // 速度
            LinearLayout spdField = makeField("速度 (Speed)", "--");
            spdValue = (TextView) spdField.getChildAt(1);
            card.addView(spdField);

            // 省份
            LinearLayout provField = makeField("所在省份", "未知");
            provinceText = (TextView) provField.getChildAt(1);
            card.addView(provField);

            // 方向提示
            LinearLayout dirField = makeField("移动方向", "静止");
            directionText = (TextView) dirField.getChildAt(1);
            directionText.setTextColor(Color.parseColor("#ffd93d")); // 黄色
            card.addView(dirField);

            root.addView(card);

            // 按钮区
            LinearLayout btnRow = new LinearLayout(this);
            btnRow.setOrientation(LinearLayout.HORIZONTAL);
            int spacing = 10;

            startBtn = makeButton("🚀 开始定位", Color.parseColor("#667eea"));
            stopBtn = makeButton("⏹️ 停止", Color.parseColor("#ff6b6b"));
            clearBtn = makeButton("🗑️ 清空", Color.parseColor("#444444"));

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

            // 地图标题
            TextView mapTitle = new TextView(this);
            mapTitle.setText("🗺️ 离线地图");
            mapTitle.setTextSize(18);
            mapTitle.setTextColor(Color.WHITE);
            mapTitle.setPadding(0, 20, 0, 10);
            root.addView(mapTitle);

            // 地图显示
            mapView = new ImageView(this);
            mapView.setBackgroundColor(Color.parseColor("#16213e"));
            LinearLayout.LayoutParams mapParams = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, 400);
            mapView.setLayoutParams(mapParams);
            root.addView(mapView);

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
            Log.d(TAG, "setContentView done");

            // 初始化地图和推断器
            provinceMap = new ProvinceMap(this);
            inferencer = new ProvinceInferencer(this);
            locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
            if (locationManager == null) {
                Log.e(TAG, "LocationManager is null!");
                Toast.makeText(this, "定位服务不可用", Toast.LENGTH_LONG).show();
            } else {
                Log.d(TAG, "LocationManager obtained");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "onCreate error", e);
            Toast.makeText(this, "启动失败: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
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
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1);
        btn.setLayoutParams(params);
        return btn;
    }

    @SuppressLint("MissingPermission")
    private void startTracking() {
        try {
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
            Log.d(TAG, "startTracking: location updates requested");
        } catch (Exception e) {
            Log.e(TAG, "startTracking error", e);
            Toast.makeText(this, "启动定位失败: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void stopTracking() {
        isTracking = false;
        startBtn.setEnabled(true);
        stopBtn.setEnabled(false);
        statusText.setText("● 已停止");
        statusText.setTextColor(Color.RED);
        
        if (locationManager != null) {
            try {
                locationManager.removeUpdates(this);
            } catch (Exception e) {
                Log.e(TAG, "stopTracking error", e);
            }
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

        try {
            double lat = location.getLatitude();
            double lon = location.getLongitude();
            float acc = location.getAccuracy();
            double alt = location.getAltitude();
            float spd = location.getSpeed();

            // 更新 UI
            latValue.setText(String.format("%.6f°", lat));
            lonValue.setText(String.format("%.6f°", lon));
            accValue.setText(String.format("%.1f 米", acc));
            altValue.setText(String.format("%.1f 米", alt));
            spdValue.setText(String.format("%.1f km/h", spd * 3.6));

            // 省份推断（每10秒采样一次）
            ProvinceInferencer.InferenceResult result = inferencer.update(lat, lon, System.currentTimeMillis());
            provinceText.setText(result.currentProvince);
            directionText.setText(result.direction.isEmpty() ? "静止" : result.direction);

            statusText.setText("● GPS 定位成功");
            statusText.setTextColor(Color.GREEN);

            // 更新地图
            Bitmap mapBmp = provinceMap.getMapBitmap(lat, lon);
            if (mapBmp != null) {
                mapView.setImageBitmap(mapBmp);
            }

            // 添加到历史
            String time = new SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(new Date());
            String dir = result.direction.isEmpty() ? "" : " " + result.direction;
            String record = String.format("%s  %.6f, %.6f (%s)%s", time, lat, lon, 
                    result.currentProvince, dir);
            historyList.add(0, record);
            if (historyList.size() > 50) historyList.remove(historyList.size() - 1);

            // 更新历史显示
            handler.post(() -> {
                try {
                    historyContainer.removeAllViews();
                    for (String line : historyList) {
                        TextView tv = new TextView(this);
                        tv.setText(line);
                        tv.setTextSize(12);
                        tv.setTextColor(Color.LTGRAY);
                        tv.setPadding(0, 5, 0, 5);
                        historyContainer.addView(tv);
                    }
                } catch (Exception e) {
                    Log.e(TAG, "update history error", e);
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "onLocationChanged error", e);
        }
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
