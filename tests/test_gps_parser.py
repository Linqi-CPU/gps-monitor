"""
GPS NMEA 解析工具 - 单元测试

测试覆盖：
- NMEA 语句解析
- 坐标转换
- 距离计算
- 方位角计算
- KML 导出
"""

import unittest
import os
import tempfile
from datetime import time

# 导入被测试的模块
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmea_parser import NMEAParser, NMEASentence, GGAData, RMCData, GLLData, GSAData, GSVData
from gps_calculator import GPSCalculator
from kml_exporter import KMLExporter


class TestNMEAParser(unittest.TestCase):
    """NMEA 解析器测试"""

    def setUp(self):
        """测试前的初始化"""
        self.parser = NMEAParser()

    def test_calculate_checksum(self):
        """测试校验和计算"""
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
        checksum = self.parser.calculate_checksum(sentence)
        self.assertEqual(checksum, 0x47)

    def test_validate_checksum_valid(self):
        """测试有效校验和验证"""
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
        self.assertTrue(self.parser.validate_checksum(sentence))

    def test_validate_checksum_invalid(self):
        """测试无效校验和验证"""
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*00"
        self.assertFalse(self.parser.validate_checksum(sentence))

    def test_convert_to_decimal_degrees_north(self):
        """测试北纬坐标转换"""
        result = self.parser._convert_to_decimal_degrees("4807.038", "N")
        expected = 48.1173  # 48° + 7.038'/60
        self.assertAlmostEqual(result, expected, places=4)

    def test_convert_to_decimal_degrees_south(self):
        """测试南纬坐标转换"""
        result = self.parser._convert_to_decimal_degrees("4807.038", "S")
        expected = -48.1173
        self.assertAlmostEqual(result, expected, places=4)

    def test_convert_to_decimal_degrees_east(self):
        """测试东经坐标转换"""
        result = self.parser._convert_to_decimal_degrees("01131.000", "E")
        expected = 11.5167  # 11° + 31'/60
        self.assertAlmostEqual(result, expected, places=4)

    def test_convert_to_decimal_degrees_west(self):
        """测试西经坐标转换"""
        result = self.parser._convert_to_decimal_degrees("01131.000", "W")
        expected = -11.5167
        self.assertAlmostEqual(result, expected, places=4)

    def test_parse_gga(self):
        """测试 GPGGA 语句解析"""
        sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
        result = self.parser.parse_sentence(sentence)
        
        self.assertIsInstance(result, GGAData)
        self.assertEqual(result.sentence_type, "GPGGA")
        self.assertEqual(result.talker, "GP")
        self.assertTrue(result.checksum_valid)
        self.assertEqual(result.fix_time, time(12, 35, 19))
        self.assertAlmostEqual(result.latitude, 48.1173, places=4)
        self.assertEqual(result.latitude_dir, "N")
        self.assertAlmostEqual(result.longitude, 11.5167, places=4)
        self.assertEqual(result.longitude_dir, "E")
        self.assertEqual(result.fix_quality, 1)
        self.assertEqual(result.num_satellites, 8)
        self.assertAlmostEqual(result.hdop, 0.9, places=1)
        self.assertAlmostEqual(result.altitude, 545.4, places=1)
        self.assertEqual(result.altitude_unit, "M")

    def test_parse_rmc(self):
        """测试 GPRMC 语句解析"""
        sentence = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
        result = self.parser.parse_sentence(sentence)
        
        self.assertIsInstance(result, RMCData)
        self.assertEqual(result.sentence_type, "GPRMC")
        self.assertEqual(result.fix_time, time(12, 35, 19))
        self.assertEqual(result.status, "A")
        self.assertAlmostEqual(result.latitude, 48.1173, places=4)
        self.assertEqual(result.latitude_dir, "N")
        self.assertAlmostEqual(result.longitude, 11.5167, places=4)
        self.assertEqual(result.longitude_dir, "E")
        self.assertAlmostEqual(result.speed_knots, 22.4, places=1)
        self.assertAlmostEqual(result.track_angle, 84.4, places=1)

    def test_parse_gll(self):
        """测试 GPGLL 语句解析"""
        sentence = "$GPGLL,4807.038,N,01131.000,E,123519,A*2C"
        result = self.parser.parse_sentence(sentence)
        
        self.assertIsInstance(result, GLLData)
        self.assertEqual(result.sentence_type, "GPGLL")
        self.assertAlmostEqual(result.latitude, 48.1173, places=4)
        self.assertEqual(result.latitude_dir, "N")
        self.assertAlmostEqual(result.longitude, 11.5167, places=4)
        self.assertEqual(result.longitude_dir, "E")
        self.assertEqual(result.fix_time, time(12, 35, 19))
        self.assertEqual(result.status, "A")

    def test_parse_invalid_sentence(self):
        """测试无效语句解析"""
        sentence = "INVALID_SENTENCE"
        result = self.parser.parse_sentence(sentence)
        self.assertIsNone(result)

    def test_parse_unknown_sentence_type(self):
        """测试未知语句类型"""
        sentence = "$GPUNK,123519,A*00"
        result = self.parser.parse_sentence(sentence)
        self.assertIsInstance(result, NMEASentence)
        self.assertEqual(result.sentence_type, "GPUNK")

    def test_parse_file(self):
        """测试文件解析"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nmea', delete=False) as f:
            f.write("$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\n")
            f.write("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A\n")
            temp_file = f.name
        
        try:
            sentences = self.parser.parse_file(temp_file)
            self.assertEqual(len(sentences), 2)
        finally:
            os.unlink(temp_file)

    def test_get_positions(self):
        """测试位置提取"""
        sentences = [
            "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47",
            "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A",
        ]
        parsed = [self.parser.parse_sentence(s) for s in sentences]
        positions = self.parser.get_positions(parsed)
        
        self.assertEqual(len(positions), 2)
        self.assertAlmostEqual(positions[0]['latitude'], 48.1173, places=4)
        self.assertAlmostEqual(positions[0]['longitude'], 11.5167, places=4)


class TestGPSCalculator(unittest.TestCase):
    """GPS 计算器测试"""

    def setUp(self):
        """测试前的初始化"""
        self.calculator = GPSCalculator()

    def test_haversine_distance_same_point(self):
        """测试同一点的距离"""
        distance = self.calculator.haversine_distance(0, 0, 0, 0)
        self.assertAlmostEqual(distance, 0, places=5)

    def test_haversine_distance_known(self):
        """测试已知距离（北京到上海）"""
        # 北京: 39.9042°N, 116.4074°E
        # 上海: 31.2304°N, 121.4737°E
        # 实际距离约 1067 km
        distance = self.calculator.haversine_distance(
            39.9042, 116.4074,
            31.2304, 121.4737
        )
        self.assertAlmostEqual(distance, 1067, delta=50)

    def test_haversine_distance_units(self):
        """测试不同单位的距离计算"""
        # 测试海里
        distance_nm = self.calculator.haversine_distance(
            39.9042, 116.4074,
            31.2304, 121.4737,
            unit='nm'
        )
        self.assertAlmostEqual(distance_nm, 575.7, delta=30)
        
        # 测试英里
        distance_miles = self.calculator.haversine_distance(
            39.9042, 116.4074,
            31.2304, 121.4737,
            unit='miles'
        )
        self.assertAlmostEqual(distance_miles, 663.5, delta=30)

    def test_bearing(self):
        """测试方位角计算"""
        # 北京到上海的方位角约为 153.1°（东南方向）
        bearing = self.calculator.bearing(
            39.9042, 116.4074,
            31.2304, 121.4737
        )
        self.assertAlmostEqual(bearing, 153.1, delta=5)

    def test_bearing_normalized(self):
        """测试方位角归一化"""
        # 测试方位角在 0°-360° 范围内
        bearing = self.calculator.bearing(0, 0, 1, 1)
        self.assertGreaterEqual(bearing, 0)
        self.assertLess(bearing, 360)

    def test_destination_point(self):
        """测试终点坐标计算"""
        # 从北京出发，向南 100km
        lat, lon = self.calculator.destination_point(39.9042, 116.4074, 100, 180)
        
        # 纬度应该减少约 0.9°
        self.assertLess(lat, 39.9042)
        self.assertAlmostEqual(lat, 39.004, delta=0.5)

    def test_convert_to_decimal_degrees(self):
        """测试坐标转换"""
        result = GPSCalculator.convert_to_decimal_degrees("4807.038", "N")
        self.assertAlmostEqual(result, 48.1173, places=4)

    def test_format_coordinate(self):
        """测试坐标格式化"""
        lat_str, lon_str = GPSCalculator.format_coordinate(39.9042, 116.4074)
        self.assertIn("N", lat_str)
        self.assertIn("E", lon_str)
        self.assertIn("°", lat_str)
        self.assertIn("°", lon_str)


class TestKMLExporter(unittest.TestCase):
    """KML 导出器测试"""

    def setUp(self):
        """测试前的初始化"""
        self.exporter = KMLExporter()

    def test_add_placemark(self):
        """测试添加位置标记"""
        self.exporter.add_placemark("Test", 39.9042, 116.4074, 100, "Description")
        self.assertEqual(len(self.exporter.places), 1)
        self.assertEqual(self.exporter.places[0]['name'], "Test")
        self.assertEqual(self.exporter.places[0]['latitude'], 39.9042)

    def test_add_track(self):
        """测试添加轨迹"""
        points = [(39.9042, 116.4074), (31.2304, 121.4737)]
        self.exporter.add_track(points, "Track 1")
        self.assertEqual(len(self.exporter.tracks), 1)
        self.assertEqual(self.exporter.tracks[0]['name'], "Track 1")

    def test_save_kml(self):
        """测试保存 KML 文件"""
        self.exporter.add_placemark("Beijing", 39.9042, 116.4074)
        points = [(39.9042, 116.4074), (31.2304, 121.4737)]
        self.exporter.add_track(points, "Beijing-Shanghai")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kml', delete=False) as f:
            temp_file = f.name
        
        try:
            result = self.exporter.save(temp_file)
            self.assertTrue(result)
            
            # 验证文件内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('<?xml version="1.0"', content)
                self.assertIn('<kml', content)
                self.assertIn('Beijing', content)
                self.assertIn('Beijing-Shanghai', content)
        finally:
            os.unlink(temp_file)

    def test_create_simple_kml(self):
        """测试快速创建简单 KML"""
        points = [(39.9042, 116.4074), (31.2304, 121.4737)]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kml', delete=False) as f:
            temp_file = f.name
        
        try:
            result = KMLExporter.create_simple_kml(temp_file, points, "Test Track")
            self.assertTrue(result)
            
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Test Track', content)
        finally:
            os.unlink(temp_file)

    def test_clear(self):
        """测试清除数据"""
        self.exporter.add_placemark("Test", 39.9042, 116.4074)
        self.exporter.add_track([(39.9042, 116.4074)])
        self.assertEqual(len(self.exporter.places), 1)
        self.assertEqual(len(self.exporter.tracks), 1)
        
        self.exporter.clear()
        self.assertEqual(len(self.exporter.places), 0)
        self.assertEqual(len(self.exporter.tracks), 0)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 解析 NMEA 文件
        parser = NMEAParser()
        test_sentences = [
            "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47",
            "$GPGGA,123520,4808.038,N,01132.000,E,1,08,0.9,545.4,M,46.9,M,,*42",
        ]
        
        parsed = [parser.parse_sentence(s) for s in test_sentences]
        positions = parser.get_positions(parsed)
        
        self.assertEqual(len(positions), 2)
        
        # 2. 计算距离
        calculator = GPSCalculator()
        distance = calculator.haversine_distance(
            positions[0]['latitude'], positions[0]['longitude'],
            positions[1]['latitude'], positions[1]['longitude']
        )
        self.assertGreater(distance, 0)
        
        # 3. 导出 KML
        exporter = KMLExporter()
        points = [(p['latitude'], p['longitude']) for p in positions]
        exporter.add_track(points, "Integration Test")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.kml', delete=False) as f:
            temp_file = f.name
        
        try:
            result = exporter.save(temp_file)
            self.assertTrue(result)
            
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Integration Test', content)
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
