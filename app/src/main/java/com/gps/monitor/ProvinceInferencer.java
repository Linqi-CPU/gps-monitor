package com.gps.monitor;

import android.content.Context;
import java.util.ArrayList;
import java.util.List;

public class ProvinceInferencer {
    private Context context;
    private List<Province> provinces;
    private GPSPoint lastPoint;
    private long lastSampleTime;
    private static final long SAMPLE_INTERVAL_MS = 10000; // 10秒
    private static final double EARTH_RADIUS = 6371000; // 地球半径（米）

    public ProvinceInferencer(Context context) {
        this.context = context;
        init();
    }

    private void init() {
        provinces = new ArrayList<>();
        // 用省会坐标作为省份中心，同时保留边界框
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

    /**
     * 更新 GPS 点，返回推断结果
     */
    public InferenceResult update(double lat, double lon, long timestamp) {
        GPSPoint current = new GPSPoint(lat, lon, timestamp);
        InferenceResult result = new InferenceResult();

        // 1. 如果距离上次采样不足10秒，直接返回最近省份（不推断方向）
        if (lastPoint != null && (timestamp - lastSampleTime) < SAMPLE_INTERVAL_MS) {
            result.currentProvince = findNearestProvince(lat, lon);
            result.direction = "";
            result.targetProvince = "";
            result.confidence = 0.8f;
            return result;
        }

        // 2. 记录采样点
        if (lastPoint != null) {
            // 计算速度矢量（米/秒，方向角）
            double distance = haversineDistance(lastPoint.lat, lastPoint.lon, lat, lon);
            long timeDiff = timestamp - lastPoint.timestamp;
            double speed = (timeDiff > 0) ? distance / (timeDiff / 1000.0) : 0;
            double bearing = calculateBearing(lastPoint.lat, lastPoint.lon, lat, lon);

            // 3. 速度矢量正交投影，排除不可能省份
            // 如果速度>5m/s（约18km/h），用方向过滤省份
            List<Province> candidates = provinces;
            if (speed > 5) {
                candidates = filterByDirection(lastPoint.lat, lastPoint.lon, bearing, 60);
            }

            // 4. 计算距离，找出最近的
            Province nearest = findNearestInList(lat, lon, candidates);
            result.currentProvince = nearest != null ? nearest.name : "未知区域";
            result.confidence = 0.9f;

            // 5. 预测方向：如果正朝某个省份边界移动，显示目标省份
            Province target = predictTargetProvince(lat, lon, bearing, speed);
            if (target != null && !target.name.equals(result.currentProvince)) {
                result.targetProvince = target.name;
                result.direction = "→ " + target.name;
            }
        } else {
            result.currentProvince = findNearestProvince(lat, lon);
            result.confidence = 0.7f;
        }

        lastPoint = current;
        lastSampleTime = timestamp;
        return result;
    }

    /**
     * 根据速度方向过滤省份：只保留在运动方向60度范围内的省份
     */
    private List<Province> filterByDirection(double lat, double lon, double bearing, double angleTolerance) {
        List<Province> filtered = new ArrayList<>();
        for (Province p : provinces) {
            double provBearing = calculateBearing(lat, lon, p.centerLat, p.centerLon);
            double angleDiff = Math.abs(bearing - provBearing);
            if (angleDiff > 180) angleDiff = 360 - angleDiff;
            if (angleDiff <= angleTolerance) {
                filtered.add(p);
            }
        }
        return filtered.isEmpty() ? provinces : filtered;
    }

    /**
     * 根据当前点和方向，预测目标省份
     */
    private Province predictTargetProvince(double lat, double lon, double bearing, double speed) {
        // 如果速度很慢，不预测
        if (speed < 2) return null;

        // 沿着方向延伸 50km，看落在哪个省份
        double targetDist = 50000; // 50km
        double targetLat, targetLon;
        double brng = Math.toRadians(bearing);
        double lat1 = Math.toRadians(lat);
        double lon1 = Math.toRadians(lon);

        targetLat = Math.asin(Math.sin(lat1) * Math.cos(targetDist / EARTH_RADIUS) +
                Math.cos(lat1) * Math.sin(targetDist / EARTH_RADIUS) * Math.cos(brng));
        targetLon = lon1 + Math.atan2(Math.sin(brng) * Math.sin(targetDist / EARTH_RADIUS) * Math.cos(lat1),
                Math.cos(targetDist / EARTH_RADIUS) - Math.sin(lat1) * Math.sin(targetLat));

        targetLat = Math.toDegrees(targetLat);
        targetLon = Math.toDegrees(targetLon);

        return findNearestProvince(targetLat, targetLon);
    }

    /**
     * 在列表中找最近的省份（到边界的距离）
     */
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

    /**
     * 找最近的省份
     */
    public Province findNearestProvince(double lat, double lon) {
        return findNearestInList(lat, lon, provinces);
    }

    /**
     * 计算点到省份的距离（到边界的最近距离）
     */
    private double distanceToProvince(double lat, double lon, Province p) {
        // 如果在边界框内，距离为0
        if (lon >= p.minLon && lon <= p.maxLon && lat >= p.minLat && lat <= p.maxLat) {
            return 0;
        }
        // 否则计算到边界的距离（简化：到最近边的距离）
        double dist = Double.MAX_VALUE;
        // 到左边
        if (lon < p.minLon) {
            dist = Math.min(dist, haversineDistance(lat, lon, lat, p.minLon));
        }
        // 到右边
        if (lon > p.maxLon) {
            dist = Math.min(dist, haversineDistance(lat, lon, lat, p.maxLon));
        }
        // 到下边
        if (lat < p.minLat) {
            dist = Math.min(dist, haversineDistance(lat, lon, p.minLat, lon));
        }
        // 到上边
        if (lat > p.maxLat) {
            dist = Math.min(dist, haversineDistance(lat, lon, p.maxLat, lon));
        }
        return dist;
    }

    /**
     * Haversine 距离（米）
     */
    private double haversineDistance(double lat1, double lon1, double lat2, double lon2) {
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                        Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return EARTH_RADIUS * c;
    }

    /**
     * 计算方位角（度，0-360）
     */
    private double calculateBearing(double lat1, double lon1, double lat2, double lon2) {
        double dLon = Math.toRadians(lon2 - lon1);
        double lat1Rad = Math.toRadians(lat1);
        double lat2Rad = Math.toRadians(lat2);
        double y = Math.sin(dLon) * Math.cos(lat2Rad);
        double x = Math.cos(lat1Rad) * Math.sin(lat2Rad) -
                Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);
        double bearing = Math.toDegrees(Math.atan2(y, x));
        return (bearing + 360) % 360;
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
        public String targetProvince;
        public String direction;  // "→ 省份名"
        public float confidence;  // 0-1
    }
}
