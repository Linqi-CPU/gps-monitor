package com.gps.monitor;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

public class ProvinceMap {
    private Context context;
    private Bitmap mapBitmap;
    private Paint textPaint, pointPaint, highlightPaint;
    private List<Province> provinces;
    
    // 中国地图范围
    private static final double MIN_LON = 73;
    private static final double MAX_LON = 135;
    private static final double MIN_LAT = 18;
    private static final double MAX_LAT = 54;
    
    public ProvinceMap(Context context) {
        this.context = context;
        init();
    }
    
    private void init() {
        // 加载地图图片
        try {
            InputStream is = context.getAssets().open("china_map.png");
            mapBitmap = BitmapFactory.decodeStream(is);
            is.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        
        // 初始化画笔
        textPaint = new Paint();
        textPaint.setColor(Color.WHITE);
        textPaint.setTextSize(30);
        textPaint.setAntiAlias(true);
        
        pointPaint = new Paint();
        pointPaint.setColor(Color.RED);
        pointPaint.setAntiAlias(true);
        
        highlightPaint = new Paint();
        highlightPaint.setColor(Color.parseColor("#667eea"));
        highlightPaint.setAlpha(100);
        highlightPaint.setAntiAlias(true);
        
        // 省份数据（从 Python 文件同步，实际部署时从 JSON 读取）
        provinces = new ArrayList<>();
        provinces.add(new Province("北京", 115.4, 117.5, 39.4, 41.6, 116.4, 39.9));
        provinces.add(new Province("天津", 116.7, 118.0, 38.5, 40.3, 117.2, 39.1));
        provinces.add(new Province("河北", 113.0, 119.8, 36.0, 42.6, 114.5, 38.0));
        provinces.add(new Province("山西", 110.2, 114.6, 34.3, 40.7, 112.5, 37.9));
        provinces.add(new Province("内蒙古", 97.2, 126.0, 37.4, 53.4, 111.7, 40.8));
        provinces.add(new Province("辽宁", 118.8, 125.8, 38.7, 43.5, 123.4, 41.8));
        provinces.add(new Province("吉林", 121.6, 131.3, 40.8, 46.3, 125.3, 43.9));
        provinces.add(new Province("黑龙江", 121.2, 135.1, 43.4, 53.6, 126.6, 45.8));
        provinces.add(new Province("上海", 120.8, 122.2, 30.7, 31.9, 121.5, 31.2));
        provinces.add(new Province("江苏", 116.3, 122.0, 30.7, 35.1, 118.8, 32.1));
        provinces.add(new Province("浙江", 118.0, 123.2, 27.0, 31.3, 120.2, 30.3));
        provinces.add(new Province("安徽", 114.9, 119.6, 29.4, 34.6, 117.3, 31.9));
        provinces.add(new Province("福建", 115.8, 120.8, 23.5, 28.3, 119.3, 26.1));
        provinces.add(new Province("江西", 113.5, 118.5, 24.5, 30.2, 115.9, 28.7));
        provinces.add(new Province("山东", 114.8, 122.7, 34.4, 38.4, 117.0, 36.7));
        provinces.add(new Province("河南", 110.3, 116.8, 31.3, 36.4, 113.7, 34.8));
        provinces.add(new Province("湖北", 108.3, 116.1, 29.0, 33.3, 114.3, 30.5));
        provinces.add(new Province("湖南", 108.7, 114.3, 24.6, 30.2, 113.0, 28.2));
        provinces.add(new Province("广东", 109.7, 117.3, 20.2, 25.5, 113.3, 23.1));
        provinces.add(new Province("广西", 104.5, 112.0, 20.9, 26.4, 108.3, 22.8));
        provinces.add(new Province("海南", 108.6, 111.1, 18.1, 20.2, 110.4, 20.0));
        provinces.add(new Province("重庆", 105.3, 110.2, 28.1, 32.3, 106.5, 29.6));
        provinces.add(new Province("四川", 97.3, 108.5, 26.0, 34.3, 104.1, 30.7));
        provinces.add(new Province("贵州", 103.6, 109.1, 24.5, 29.3, 106.7, 26.6));
        provinces.add(new Province("云南", 97.5, 106.2, 21.1, 29.3, 102.7, 25.0));
        provinces.add(new Province("西藏", 78.4, 99.1, 26.9, 36.4, 91.1, 29.6));
        provinces.add(new Province("陕西", 105.5, 111.2, 31.7, 39.6, 108.9, 34.3));
        provinces.add(new Province("甘肃", 92.3, 108.7, 32.6, 42.9, 103.8, 36.1));
        provinces.add(new Province("青海", 89.4, 103.1, 31.6, 39.2, 101.8, 36.6));
        provinces.add(new Province("宁夏", 104.3, 107.7, 35.1, 39.4, 106.3, 38.5));
        provinces.add(new Province("新疆", 73.4, 96.4, 34.3, 49.2, 87.6, 43.8));
        provinces.add(new Province("台湾", 119.3, 122.0, 21.9, 25.3, 121.0, 23.5));
    }
    
    private double latLonToX(double lon) {
        return (lon - MIN_LON) / (MAX_LON - MIN_LON);
    }
    
    private double latLonToY(double lat) {
        return (MAX_LAT - lat) / (MAX_LAT - MIN_LAT);
    }
    
    public String getProvinceName(double lat, double lon) {
        for (Province p : provinces) {
            if (lon >= p.minLon && lon <= p.maxLon && lat >= p.minLat && lat <= p.maxLat) {
                return p.name;
            }
        }
        return "未知区域";
    }
    
    public Bitmap getMapBitmap(double currentLat, double currentLon) {
        if (mapBitmap == null) return null;
        
        Bitmap result = mapBitmap.copy(Bitmap.Config.ARGB_8888, true);
        Canvas canvas = new Canvas(result);
        
        // 高亮当前省份
        String currentProv = getProvinceName(currentLat, currentLon);
        for (Province p : provinces) {
            if (p.name.equals(currentProv)) {
                int x1 = (int) (latLonToX(p.minLon) * mapBitmap.getWidth());
                int y1 = (int) (latLonToY(p.maxLat) * mapBitmap.getHeight());
                int x2 = (int) (latLonToX(p.maxLon) * mapBitmap.getWidth());
                int y2 = (int) (latLonToY(p.minLat) * mapBitmap.getHeight());
                canvas.drawRect(x1, y1, x2, y2, highlightPaint);
                break;
            }
        }
        
        // 绘制当前位置点
        int px = (int) (latLonToX(currentLon) * mapBitmap.getWidth());
        int py = (int) (latLonToY(currentLat) * mapBitmap.getHeight());
        canvas.drawCircle(px, py, 8, pointPaint);
        
        // 标签
        canvas.drawText(currentProv, px + 15, py - 15, textPaint);
        
        return result;
    }
    
    public static class Province {
        public String name;
        public double minLon, maxLon, minLat, maxLat;
        public double capitalLon, capitalLat;
        
        public Province(String name, double minLon, double maxLon, double minLat, double maxLat, 
                        double capitalLon, double capitalLat) {
            this.name = name;
            this.minLon = minLon;
            this.maxLon = maxLon;
            this.minLat = minLat;
            this.maxLat = maxLat;
            this.capitalLon = capitalLon;
            this.capitalLat = capitalLat;
        }
    }
}
