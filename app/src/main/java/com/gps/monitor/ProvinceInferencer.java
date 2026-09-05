package com.gps.monitor;

import android.content.Context;
import java.util.ArrayList;
import java.util.List;

public class ProvinceInferencer {
    public enum Algorithm {
        BOUNDS,     // 矩形边界框
        VECTOR,     // 速度矢量+距离
        HYBRID      // 两种对比，取更可信的
    }

    private Context context;
    private List<Province> provinces;
    private GPSPoint lastPoint;
    private long lastSampleTime;
    private Algorithm currentAlgo;
    private static final long SAMPLE_INTERVAL_MS = 10000;
    private static final double EARTH_RADIUS = 6371000;

    public ProvinceInferencer(Context context) {
        this.context = context;
        this.currentAlgo = Algorithm.BOUNDS; // 默认矩形
        init();
    }

    public void setAlgorithm(Algorithm algo) {
        this.currentAlgo = algo;
    }

    public Algorithm getAlgorithm() {
        return currentAlgo;
    }

    private void init() {
        provinces = new ArrayList<>();
        provinces.add(new Province("北京", 116.4, 39.9, 115.4, 117.5, 39.4, 41.6));
        provinces.add(new Province("天津", 117.2, 39.1, 116.7, 118.0, 38.5, 40.3));
        provinces.add(new Province("河北", 114.5, 38.0, 113.0, 119.8, 36.0, 42.6));
        provinces.add(new Province("山西", 112.5, 37.9, 110.2, 114.6, 34.3, 40.7));
        provinces.add(new Province("内蒙古", 111.7, 40.8, 97.2, 126.0, 37.4, 53.4));
        provinces.add(new Province("辽宁", 123.4, 41.8, 118.8, 125.8, 38.7, 43.5));
        provinces.add(new Province("吉林", 125.3, 43.9, 121.6, 131.3, 40.8, 46.3));
        provinces.add(new Province("黑龙江", 126.6, 45.8, 121.2, 135.1, 43.4, 53.6));
        provinces.add(new Province("上海", 121.5, 31.2, 120.8, 122.2, 30.7, 31.9));
        provinces.add(new Province("江苏", 118.8, 32.1, 116.3, 122.0, 30.7, 35.1));
        provinces.add(new Province("浙江", 120.2, 30.3, 118.0, 123.2, 27.0, 31.3));
        provinces.add(new Province("安徽", 117.3, 31.9, 114.9, 119.6, 29.4, 34.6));
        provinces.add(new Province("福建", 119.3, 26.1, 115.8, 120.8, 23.5, 28.3));
        provinces.add(new Province("江西", 115.9, 28.7, 113.5, 118.5, 24.5, 30.2));
        provinces.add(new Province("山东", 117.0, 36.7, 114.8, 122.7, 34.4, 38.4));
        provinces.add(new Province("河南", 113.7, 34.8, 110.3, 116.8, 31.3, 36.4));
        provinces.add(new Province("湖北", 114.3, 30.5, 108.3, 116.1, 29.0, 33.3));
        provinces.add(new Province("湖南", 113.0, 28.2, 108.7, 114.3, 24.6, 30.2));
        provinces.add(new Province("广东", 113.3, 23.1, 109.7, 117.3, 20.2, 25.5));
        provinces.add(new Province("广西", 108.3, 22.8, 104.5, 112.0, 20.9, 26.4));
        provinces.add(new Province("海南", 110.4, 20.0, 108.6, 111.1, 18.1, 20.2));
        provinces.add(new Province("重庆", 106.5, 29.6, 105.3, 110.2, 28.1, 32.3));
        provinces.add(new Province("四川", 104.1, 30.7, 97.3, 108.5, 26.0, 34.3));
        provinces.add(new Province("贵州", 106.7, 26.6, 103.6, 109.1, 24.5, 29.3));
        provinces.add(new Province("云南", 102.7, 25.0, 97.5, 106.2, 21.1, 29.3));
        provinces.add(new Province("西藏", 91.1, 29.6, 78.4, 99.1, 26.9, 36.4));
        provinces.add(new Province("陕西", 108.9, 34.3, 105.5, 111.2, 31.7, 39.6));
        provinces.add(new Province("甘肃", 103.8, 36.1, 92.3, 108.7, 32.6, 42.9));
        provinces.add(new Province("青海", 101.8, 36.6, 89.4, 103.1, 31.6, 39.2));
        provinces.add(new Province("宁夏", 106.3, 38.5, 104.3, 107.7, 35.1, 39.4));
        provinces.add(new Province("新疆", 87.6, 43.8, 73.4, 96.4, 34.3, 49.2));
        provinces.add(new Province("台湾", 121.0, 23.5, 119.3, 122.0, 21.9, 25.3));
    }

    public InferenceResult update(double lat, double lon, long timestamp) {
        InferenceResult result = new InferenceResult();

        // 矩形算法
        Province boundsResult = findProvinceByBounds(lat, lon);
        result.boundsProvince = boundsResult != null ? boundsResult.name : "未知";
        result.boundsDistance = boundsResult != null ? distanceToProvince(lat, lon, boundsResult) : -1;

        // 矢量算法
        Province vectorResult = null;
        String direction = "";
        if (lastPoint != null && (timestamp - lastSampleTime) >= SAMPLE_INTERVAL_MS) {
            double distance = haversineDistance(lastPoint.lat, lastPoint.lon, lat, lon);
            long timeDiff = timestamp - lastPoint.timestamp;
            double speed = (timeDiff > 0) ? distance / (timeDiff / 1000.0) : 0;
            double bearing = calculateBearing(lastPoint.lat, lastPoint.lon, lat, lon);

            List<Province> candidates = provinces;
            if (speed > 5) {
                candidates = filterByDirection(lastPoint.lat, lastPoint.lon, bearing, 60);
            }
            vectorResult = findNearestInList(lat, lon, candidates);
            Province target = predictTargetProvince(lat, lon, bearing, speed);
            if (target != null && !target.name.equals(vectorResult != null ? vectorResult.name : "")) {
                direction = "→ " + target.name;
            }
            lastPoint = new GPSPoint(lat, lon, timestamp);
            lastSampleTime = timestamp;
        } else {
            if (lastPoint == null) {
                lastPoint = new GPSPoint(lat, lon, timestamp);
                lastSampleTime = timestamp;
            }
            vectorResult = findNearestProvince(lat, lon);
        }

        result.vectorProvince = vectorResult != null ? vectorResult.name : "未知";
        result.direction = direction;

        // 根据模式选择最终结果
        switch (currentAlgo) {
            case BOUNDS:
                result.currentProvince = result.boundsProvince;
                break;
            case VECTOR:
                result.currentProvince = result.vectorProvince;
                break;
            case HYBRID:
                // 对比两种：如果差距大，取距离更近的；如果都在边界，用距离
                if (!result.boundsProvince.equals(result.vectorProvince)) {
                    // 不一致，取距离边界更近的
                    result.currentProvince = result.boundsDistance < 0 ? result.vectorProvince : 
                            result.boundsDistance < 10000 ? result.boundsProvince : result.vectorProvince;
                    result.confidence = 0.5f; // 低置信度
                } else {
                    result.currentProvince = result.boundsProvince;
                    result.confidence = 0.9f;
                }
                break;
        }
        return result;
    }

    // ---- 矩形边界算法 ----
    private Province findProvinceByBounds(double lat, double lon) {
        for (Province p : provinces) {
            if (lon >= p.minLon && lon <= p.maxLon && lat >= p.minLat && lat <= p.maxLat) {
                return p;
            }
        }
        return null;
    }

    // ---- 矢量算法 ----
    private List<Province> filterByDirection(double lat, double lon, double bearing, double angleTolerance) {
        List<Province> filtered = new ArrayList<>();
        for (Province p : provinces) {
            double provBearing = calculateBearing(lat, lon, p.centerLat, p.centerLon);
            double angleDiff = Math.abs(bearing - provBearing);
            if (angleDiff > 180) angleDiff = 360 - angleDiff;
            if (angleDiff <= angleTolerance) filtered.add(p);
        }
        return filtered.isEmpty() ? provinces : filtered;
    }

    private Province predictTargetProvince(double lat, double lon, double bearing, double speed) {
        if (speed < 2) return null;
        double targetDist = 50000;
        double brng = Math.toRadians(bearing);
        double lat1 = Math.toRadians(lat);
        double lon1 = Math.toRadians(lon);
        double targetLat = Math.asin(Math.sin(lat1) * Math.cos(targetDist / EARTH_RADIUS) +
                Math.cos(lat1) * Math.sin(targetDist / EARTH_RADIUS) * Math.cos(brng));
        double targetLon = lon1 + Math.atan2(Math.sin(brng) * Math.sin(targetDist / EARTH_RADIUS) * Math.cos(lat1),
                Math.cos(targetDist / EARTH_RADIUS) - Math.sin(lat1) * Math.sin(targetLat));
        return findNearestProvince(Math.toDegrees(targetLat), Math.toDegrees(targetLon));
    }

    // ---- 公共方法 ----
    private Province findNearestInList(double lat, double lon, List<Province> list) {
        Province nearest = null;
        double minDist = Double.MAX_VALUE;
        for (Province p : list) {
            double dist = distanceToProvince(lat, lon, p);
            if (dist < minDist) {
                minDist = dist;
                nearest = p;
            }
        }
        return nearest;
    }

    public Province findNearestProvince(double lat, double lon) {
        return findNearestInList(lat, lon, provinces);
    }

    private double distanceToProvince(double lat, double lon, Province p) {
        if (lon >= p.minLon && lon <= p.maxLon && lat >= p.minLat && lat <= p.maxLat) return 0;
        double dist = Double.MAX_VALUE;
        if (lon < p.minLon) dist = Math.min(dist, haversineDistance(lat, lon, lat, p.minLon));
        if (lon > p.maxLon) dist = Math.min(dist, haversineDistance(lat, lon, lat, p.maxLon));
        if (lat < p.minLat) dist = Math.min(dist, haversineDistance(lat, lon, p.minLat, lon));
        if (lat > p.maxLat) dist = Math.min(dist, haversineDistance(lat, lon, p.maxLat, lon));
        return dist;
    }

    private double haversineDistance(double lat1, double lon1, double lat2, double lon2) {
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat/2)*Math.sin(dLat/2) +
                Math.cos(Math.toRadians(lat1))*Math.cos(Math.toRadians(lat2)) *
                        Math.sin(dLon/2)*Math.sin(dLon/2);
        return EARTH_RADIUS * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }

    private double calculateBearing(double lat1, double lon1, double lat2, double lon2) {
        double dLon = Math.toRadians(lon2 - lon1);
        double lat1Rad = Math.toRadians(lat1);
        double lat2Rad = Math.toRadians(lat2);
        double y = Math.sin(dLon) * Math.cos(lat2Rad);
        double x = Math.cos(lat1Rad) * Math.sin(lat2Rad) -
                Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);
        return (Math.toDegrees(Math.atan2(y, x)) + 360) % 360;
    }

    public static class Province {
        public String name;
        public double centerLon, centerLat;
        public double minLon, maxLon, minLat, maxLat;
        public Province(String name, double centerLon, double centerLat,
                        double minLon, double maxLon, double minLat, double maxLat) {
            this.name = name;
            this.centerLon = centerLon;
            this.centerLat = centerLat;
            this.minLon = minLon;
            this.maxLon = maxLon;
            this.minLat = minLat;
            this.maxLat = maxLat;
        }
    }

    public static class GPSPoint {
        public double lat, lon;
        public long timestamp;
        public GPSPoint(double lat, double lon, long timestamp) {
            this.lat = lat;
            this.lon = lon;
            this.timestamp = timestamp;
        }
    }

    public static class InferenceResult {
        public String currentProvince;
        public String boundsProvince;
        public String vectorProvince;
        public String direction;
        public double boundsDistance;
        public float confidence;
    }
}
