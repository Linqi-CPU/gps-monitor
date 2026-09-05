"""
GPS 坐标计算工具模块

提供以下功能：
- Haversine 公式计算两点间的大圆距离
- 计算两点间的初始方位角
- 坐标格式转换
"""

import math
from typing import Tuple


class GPSCalculator:
    """GPS 坐标计算器"""

    # 地球平均半径（单位：千米）
    EARTH_RADIUS_KM = 6371.0
    # 地球平均半径（单位：海里）
    EARTH_RADIUS_NM = 3440.065
    # 地球平均半径（单位：英里）
    EARTH_RADIUS_MILES = 3958.8

    @staticmethod
    def haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        unit: str = 'km'
    ) -> float:
        """
        使用 Haversine 公式计算两个经纬度坐标点之间的大圆距离
        
        Args:
            lat1: 起点纬度（十进制度数）
            lon1: 起点经度（十进制度数）
            lat2: 终点纬度（十进制度数）
            lon2: 终点经度（十进制度数）
            unit: 距离单位，可选 'km'（千米）、'nm'（海里）、'miles'（英里）
        
        Returns:
            两点间的大圆距离
        
        Example:
            >>> calculator = GPSCalculator()
            >>> # 北京到上海的距离
            >>> distance = calculator.haversine_distance(39.9042, 116.4074, 31.2304, 121.4737)
            >>> print(f"距离: {distance:.2f} km")
            距离: 1067.52 km
        """
        # 将十进制度数转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # 差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine 公式
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # 选择地球半径
        if unit == 'nm':
            radius = GPSCalculator.EARTH_RADIUS_NM
        elif unit == 'miles':
            radius = GPSCalculator.EARTH_RADIUS_MILES
        else:
            radius = GPSCalculator.EARTH_RADIUS_KM

        distance = radius * c
        return distance

    @staticmethod
    def bearing(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        计算从点 1 到点 2 的初始方位角（以正北为 0°，顺时针方向）
        
        Args:
            lat1: 起点纬度（十进制度数）
            lon1: 起点经度（十进制度数）
            lat2: 终点纬度（十进制度数）
            lon2: 终点经度（十进制度数）
        
        Returns:
            初始方位角（0°-360°，以正北为 0°）
        
        Example:
            >>> calculator = GPSCalculator()
            >>> # 北京到上海的方位角
            >>> bearing = calculator.bearing(39.9042, 116.4074, 31.2304, 121.4737)
            >>> print(f"方位角: {bearing:.1f}°")
            方位角: 195.6°
        """
        # 将十进制度数转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # 经度差
        dlon = lon2_rad - lon1_rad

        # 方位角计算
        x = math.sin(dlon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - \
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)

        bearing_rad = math.atan2(x, y)
        bearing_deg = math.degrees(bearing_rad)

        # 归一化到 0°-360°
        bearing_deg = (bearing_deg + 360) % 360

        return bearing_deg

    @staticmethod
    def destination_point(
        lat: float,
        lon: float,
        distance_km: float,
        bearing_deg: float
    ) -> Tuple[float, float]:
        """
        根据起点、距离和方位角计算终点坐标
        
        Args:
            lat: 起点纬度（十进制度数）
            lon: 起点经度（十进制度数）
            distance_km: 距离（千米）
            bearing_deg: 方位角（度，正北为 0°）
        
        Returns:
            (终点纬度, 终点经度)
        """
        # 将十进制度数转换为弧度
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        bearing_rad = math.radians(bearing_deg)

        # 角距离
        angular_distance = distance_km / GPSCalculator.EARTH_RADIUS_KM

        # 计算终点纬度
        dest_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(angular_distance) +
            math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
        )

        # 计算终点经度
        dest_lon_rad = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
            math.cos(angular_distance) - math.sin(lat_rad) * math.sin(dest_lat_rad)
        )

        # 转换回十进制度数
        dest_lat = math.degrees(dest_lat_rad)
        dest_lon = math.degrees(dest_lon_rad)

        # 归一化经度到 -180° 到 180°
        dest_lon = (dest_lon + 540) % 360 - 180

        return dest_lat, dest_lon

    @staticmethod
    def convert_to_decimal_degrees(nmea_coord: str, direction: str) -> float:
        """
        将 NMEA 格式的坐标转换为十进制度数（便捷方法）
        
        Args:
            nmea_coord: NMEA 格式的坐标字符串（ddmm.mmmm 或 dddmm.mmmm）
            direction: 方向 N/S/E/W
        
        Returns:
            十进制度数表示的坐标
        """
        if not nmea_coord:
            return None

        # 确定度数的位数
        if direction in ['N', 'S']:
            # 纬度：2 位度数
            degrees = int(nmea_coord[:2])
            minutes = float(nmea_coord[2:])
        else:
            # 经度：3 位度数
            degrees = int(nmea_coord[:3])
            minutes = float(nmea_coord[3:])

        decimal = degrees + minutes / 60.0

        # 南纬和西经为负值
        if direction in ['S', 'W']:
            decimal = -decimal

        return decimal

    @staticmethod
    def format_coordinate(lat: float, lon: float) -> Tuple[str, str]:
        """
        将十进制度数格式化为人类可读的坐标字符串
        
        Args:
            lat: 纬度（十进制度数）
            lon: 经度（十进制度数）
        
        Returns:
            (纬度字符串, 经度字符串)
        """
        def format_single(value: float, positive: str, negative: str) -> str:
            direction = positive if value >= 0 else negative
            abs_value = abs(value)
            degrees = int(abs_value)
            minutes = (abs_value - degrees) * 60
            seconds = (minutes - int(minutes)) * 60
            return f"{degrees}°{int(minutes)}'{seconds:.2f}\"{direction}"

        lat_str = format_single(lat, 'N', 'S')
        lon_str = format_single(lon, 'E', 'W')

        return lat_str, lon_str
