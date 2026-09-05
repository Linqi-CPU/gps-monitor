"""
NMEA 语句解析器模块

支持解析标准 NMEA 0183 协议中的常见 GPS 语句：
- GPGGA: 全球定位系统固定数据
- GPRMC: 推荐定位数据
- GPGLL: 地理定位信息
- GPGSA: GPS DOP 和活动卫星
- GPGSV: GPS 可见卫星
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, time


@dataclass
class NMEASentence:
    """NMEA 语句的基础数据结构"""
    sentence_type: str  # 语句类型，如 GPGGA, GPRMC
    talker: str  # 设备标识符，如 GP
    raw: str  # 原始语句
    checksum_valid: bool  # 校验和是否有效


@dataclass
class GGAData(NMEASentence):
    """GPGGA - 全球定位系统固定数据"""
    fix_time: Optional[time] = None
    latitude: Optional[float] = None  # 十进制度数
    latitude_dir: Optional[str] = None  # N 或 S
    longitude: Optional[float] = None  # 十进制度数
    longitude_dir: Optional[str] = None  # E 或 W
    fix_quality: Optional[int] = None  # 定位质量: 0=无效, 1=GPS, 2=DGPS
    num_satellites: Optional[int] = None
    hdop: Optional[float] = None  # 水平精度因子
    altitude: Optional[float] = None  # 海拔高度（米）
    altitude_unit: Optional[str] = None  # 单位 M=米
    geoid_separation: Optional[float] = None  # 大地水准面差距
    geoid_unit: Optional[str] = None
    dgps_age: Optional[float] = None
    dgps_station: Optional[str] = None


@dataclass
class RMCData(NMEASentence):
    """GPRMC - 推荐定位数据"""
    fix_time: Optional[time] = None
    status: Optional[str] = None  # A=有效, V=无效
    latitude: Optional[float] = None
    latitude_dir: Optional[str] = None
    longitude: Optional[float] = None
    longitude_dir: Optional[str] = None
    speed_knots: Optional[float] = None  # 速度（节）
    track_angle: Optional[float] = None  # 航向角（度）
    date: Optional[datetime] = None  # 日期
    mag_variation: Optional[float] = None  # 磁偏角
    mag_var_dir: Optional[str] = None  # E=东, W=西


@dataclass
class GLLData(NMEASentence):
    """GPGLL - 地理定位信息"""
    latitude: Optional[float] = None
    latitude_dir: Optional[str] = None
    longitude: Optional[float] = None
    longitude_dir: Optional[str] = None
    fix_time: Optional[time] = None
    status: Optional[str] = None  # A=有效, V=无效


@dataclass
class GSAData(NMEASentence):
    """GPGSA - GPS DOP 和活动卫星"""
    mode: Optional[str] = None  # M=手动, A=自动
    fix_type: Optional[int] = None  # 1=无, 2=2D, 3=3D
    satellites: List[int] = field(default_factory=list)  # 使用的卫星 PRN 编号
    pdop: Optional[float] = None  # 位置精度因子
    hdop: Optional[float] = None
    vdop: Optional[float] = None  # 垂直精度因子


@dataclass
class GSVData(NMEASentence):
    """GPGSV - GPS 可见卫星"""
    total_messages: Optional[int] = None  # 总消息数
    message_num: Optional[int] = None  # 当前消息编号
    num_satellites: Optional[int] = None  # 可见卫星总数
    satellites_info: List[Dict[str, Any]] = field(default_factory=list)  # 卫星详细信息


class NMEAParser:
    """NMEA 语句解析器"""

    def __init__(self):
        self.parsers = {
            'GPGGA': self._parse_gga,
            'GPRMC': self._parse_rmc,
            'GPGLL': self._parse_gll,
            'GPGSA': self._parse_gsa,
            'GPGSV': self._parse_gsv,
        }

    def calculate_checksum(self, sentence: str) -> int:
        """
        计算 NMEA 语句的校验和
        
        Args:
            sentence: 完整的 NMEA 语句（包含 $ 但不包含 *XX）
        
        Returns:
            校验和值（0-255）
        """
        checksum = 0
        # 跳过开头的 $ 符号
        for char in sentence[1:]:
            if char == '*':
                break
            checksum ^= ord(char)
        return checksum

    def validate_checksum(self, sentence: str) -> bool:
        """
        验证 NMEA 语句的校验和
        
        Args:
            sentence: 完整的 NMEA 语句
        
        Returns:
            校验和是否有效
        """
        if '*' not in sentence:
            return False

        data_part, checksum_part = sentence.rsplit('*', 1)
        try:
            expected_checksum = int(checksum_part[:2], 16)
            calculated_checksum = self.calculate_checksum(data_part)
            return expected_checksum == calculated_checksum
        except (ValueError, IndexError):
            return False

    def _convert_to_decimal_degrees(self, nmea_coord: str, direction: str) -> float:
        """
        将 NMEA 格式的坐标转换为十进制度数
        
        NMEA 格式：ddmm.mmmm（纬度）或 dddmm.mmmm（经度）
        十进制度数：dd.mmmmmm 或 ddd.mmmmmm
        
        Args:
            nmea_coord: NMEA 格式的坐标字符串
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

    def _parse_time(self, time_str: str) -> Optional[time]:
        """解析 NMEA 时间格式 HHMMSS.SSS"""
        if not time_str:
            return None
        try:
            hours = int(time_str[0:2])
            minutes = int(time_str[2:4])
            seconds = float(time_str[4:])
            return time(hours, minutes, int(seconds))
        except (ValueError, IndexError):
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析 NMEA 日期格式 DDMMYY"""
        if not date_str:
            return None
        try:
            day = int(date_str[0:2])
            month = int(date_str[2:4])
            year = int(date_str[4:6])
            # 假设 2000-2099 年
            year += 2000
            return datetime(year, month, day)
        except (ValueError, IndexError):
            return None

    def _parse_gga(self, parts: List[str]) -> GGAData:
        """解析 GPGGA 语句"""
        data = GGAData(
            sentence_type='GPGGA',
            talker='GP',
            raw=','.join(parts),
            checksum_valid=True  # 已在外部验证
        )

        if len(parts) >= 2 and parts[1]:
            data.fix_time = self._parse_time(parts[1])

        if len(parts) >= 4 and parts[2] and parts[3]:
            data.latitude = self._convert_to_decimal_degrees(parts[2], parts[3])
            data.latitude_dir = parts[3]

        if len(parts) >= 6 and parts[4] and parts[5]:
            data.longitude = self._convert_to_decimal_degrees(parts[4], parts[5])
            data.longitude_dir = parts[5]

        if len(parts) >= 7 and parts[6]:
            data.fix_quality = int(parts[6])

        if len(parts) >= 8 and parts[7]:
            data.num_satellites = int(parts[7])

        if len(parts) >= 9 and parts[8]:
            data.hdop = float(parts[8])

        if len(parts) >= 10 and parts[9]:
            data.altitude = float(parts[9])

        if len(parts) >= 11 and parts[10]:
            data.altitude_unit = parts[10]

        if len(parts) >= 12 and parts[11]:
            data.geoid_separation = float(parts[11])

        if len(parts) >= 13 and parts[12]:
            data.geoid_unit = parts[12]

        if len(parts) >= 14 and parts[13]:
            data.dgps_age = float(parts[13])

        if len(parts) >= 15 and parts[14]:
            data.dgps_station = parts[14]

        return data

    def _parse_rmc(self, parts: List[str]) -> RMCData:
        """解析 GPRMC 语句"""
        data = RMCData(
            sentence_type='GPRMC',
            talker='GP',
            raw=','.join(parts),
            checksum_valid=True
        )

        if len(parts) >= 2 and parts[1]:
            data.fix_time = self._parse_time(parts[1])

        if len(parts) >= 3 and parts[2]:
            data.status = parts[2]

        if len(parts) >= 5 and parts[3] and parts[4]:
            data.latitude = self._convert_to_decimal_degrees(parts[3], parts[4])
            data.latitude_dir = parts[4]

        if len(parts) >= 7 and parts[5] and parts[6]:
            data.longitude = self._convert_to_decimal_degrees(parts[5], parts[6])
            data.longitude_dir = parts[6]

        if len(parts) >= 8 and parts[7]:
            data.speed_knots = float(parts[7])

        if len(parts) >= 9 and parts[8]:
            data.track_angle = float(parts[8])

        if len(parts) >= 10 and parts[9]:
            data.date = self._parse_date(parts[9])

        if len(parts) >= 11 and parts[10]:
            data.mag_variation = float(parts[10])

        if len(parts) >= 12 and parts[11]:
            data.mag_var_dir = parts[11]

        return data

    def _parse_gll(self, parts: List[str]) -> GLLData:
        """解析 GPGLL 语句"""
        data = GLLData(
            sentence_type='GPGLL',
            talker='GP',
            raw=','.join(parts),
            checksum_valid=True
        )

        if len(parts) >= 3 and parts[1] and parts[2]:
            data.latitude = self._convert_to_decimal_degrees(parts[1], parts[2])
            data.latitude_dir = parts[2]

        if len(parts) >= 5 and parts[3] and parts[4]:
            data.longitude = self._convert_to_decimal_degrees(parts[3], parts[4])
            data.longitude_dir = parts[4]

        if len(parts) >= 6 and parts[5]:
            data.fix_time = self._parse_time(parts[5])

        if len(parts) >= 7 and parts[6]:
            data.status = parts[6]

        return data

    def _parse_gsa(self, parts: List[str]) -> GSAData:
        """解析 GPGSA 语句"""
        data = GSAData(
            sentence_type='GPGSA',
            talker='GP',
            raw=','.join(parts),
            checksum_valid=True
        )

        if len(parts) >= 2 and parts[1]:
            data.mode = parts[1]

        if len(parts) >= 3 and parts[2]:
            data.fix_type = int(parts[2])

        # 解析卫星 PRN 编号（字段 4-15）
        for i in range(3, 14):
            if len(parts) > i and parts[i]:
                try:
                    data.satellites.append(int(parts[i]))
                except ValueError:
                    pass

        if len(parts) >= 16 and parts[15]:
            data.pdop = float(parts[15])

        if len(parts) >= 17 and parts[16]:
            data.hdop = float(parts[16])

        if len(parts) >= 18 and parts[17]:
            data.vdop = float(parts[17])

        return data

    def _parse_gsv(self, parts: List[str]) -> GSVData:
        """解析 GPGSV 语句"""
        data = GSVData(
            sentence_type='GPGSV',
            talker='GP',
            raw=','.join(parts),
            checksum_valid=True
        )

        if len(parts) >= 2 and parts[1]:
            data.total_messages = int(parts[1])

        if len(parts) >= 3 and parts[2]:
            data.message_num = int(parts[2])

        if len(parts) >= 4 and parts[3]:
            data.num_satellites = int(parts[3])

        # 解析卫星信息（每个卫星占 4 个字段：PRN, 仰角, 方位角, 信噪比）
        i = 4
        while i + 3 < len(parts):
            if parts[i]:
                satellite = {
                    'prn': int(parts[i]) if parts[i] else None,
                    'elevation': float(parts[i + 1]) if parts[i + 1] else None,
                    'azimuth': float(parts[i + 2]) if parts[i + 2] else None,
                    'snr': float(parts[i + 3]) if parts[i + 3] else None,
                }
                data.satellites_info.append(satellite)
            i += 4

        return data

    def parse_sentence(self, sentence: str) -> Optional[NMEASentence]:
        """
        解析单个 NMEA 语句
        
        Args:
            sentence: 完整的 NMEA 语句（例如 "$GPGGA,...*XX"）
        
        Returns:
            解析后的 NMEA 数据对象，如果无法解析则返回 None
        """
        # 去除空白字符
        sentence = sentence.strip()

        # 检查是否为 NMEA 语句
        if not sentence.startswith('$'):
            return None

        # 验证校验和
        checksum_valid = self.validate_checksum(sentence)

        # 提取数据部分（去除 $ 和 *XX）
        data_part = sentence[1:]
        if '*' in data_part:
            data_part = data_part.split('*')[0]

        # 分割字段
        parts = data_part.split(',')

        if len(parts) < 2:
            return NMEASentence(
                sentence_type='UNKNOWN',
                talker='UN',
                raw=sentence,
                checksum_valid=checksum_valid
            )

        # 提取语句类型（例如 GPGGA）
        sentence_type = parts[0].lstrip('$')
        talker = sentence_type[:2] if len(sentence_type) >= 2 else 'UN'

        # 调用对应的解析函数
        parser_func = self.parsers.get(sentence_type)
        if parser_func:
            return parser_func(parts)
        else:
            return NMEASentence(
                sentence_type=sentence_type,
                talker=talker,
                raw=sentence,
                checksum_valid=checksum_valid
            )

    def parse_file(self, filepath: str) -> List[NMEASentence]:
        """
        解析 NMEA 日志文件
        
        Args:
            filepath: NMEA 文件路径
        
        Returns:
            解析后的 NMEA 语句列表
        """
        sentences = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and line.startswith('$'):
                        sentence = self.parse_sentence(line)
                        if sentence:
                            sentences.append(sentence)
        except FileNotFoundError:
            print(f"错误：文件 {filepath} 不存在")
        except Exception as e:
            print(f"错误：读取文件失败 - {e}")

        return sentences

    def get_positions(self, sentences: List[NMEASentence]) -> List[Dict[str, Any]]:
        """
        从 NMEA 语句中提取位置信息
        
        Args:
            sentences: 解析后的 NMEA 语句列表
        
        Returns:
            位置信息列表，每个元素包含 latitude, longitude, altitude, timestamp
        """
        positions = []

        for sentence in sentences:
            lat, lon, alt, timestamp = None, None, None, None

            # 从 GGA 语句提取位置
            if isinstance(sentence, GGAData) and sentence.latitude is not None:
                lat = sentence.latitude
                lon = sentence.longitude
                alt = sentence.altitude
                timestamp = sentence.fix_time

            # 从 RMC 语句提取位置
            elif isinstance(sentence, RMCData) and sentence.latitude is not None:
                lat = sentence.latitude
                lon = sentence.longitude
                timestamp = sentence.fix_time

            # 从 GLL 语句提取位置
            elif isinstance(sentence, GLLData) and sentence.latitude is not None:
                lat = sentence.latitude
                lon = sentence.longitude
                timestamp = sentence.fix_time

            if lat is not None and lon is not None:
                positions.append({
                    'latitude': lat,
                    'longitude': lon,
                    'altitude': alt,
                    'timestamp': timestamp
                })

        return positions
