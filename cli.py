"""
GPS NMEA 解析工具 - 命令行接口

提供命令行工具，支持：
- 解析 NMEA 文件
- 计算两点间距离
- 计算方位角
- 导出 KML 文件
"""

import argparse
import sys
import os

# 导入自定义模块
from nmea_parser import NMEAParser
from gps_calculator import GPSCalculator
from kml_exporter import KMLExporter


def cmd_parse(args):
    """解析 NMEA 文件"""
    if not os.path.exists(args.file):
        print(f"错误：文件 {args.file} 不存在")
        sys.exit(1)
    
    parser = NMEAParser()
    sentences = parser.parse_file(args.file)
    positions = parser.get_positions(sentences)
    
    print(f"\n文件: {args.file}")
    print(f"总语句数: {len(sentences)}")
    print(f"有效位置点: {len(positions)}")
    
    if args.verbose:
        print("\n解析的语句类型:")
        type_count = {}
        for sentence in sentences:
            type_count[sentence.sentence_type] = type_count.get(sentence.sentence_type, 0) + 1
        
        for stype, count in sorted(type_count.items()):
            print(f"  {stype}: {count}")
    
    if positions:
        print("\n前 5 个位置点:")
        for i, pos in enumerate(positions[:5]):
            lat, lon = pos['latitude'], pos['longitude']
            print(f"  {i+1}. 纬度: {lat:.6f}, 经度: {lon:.6f}")
            if pos['altitude']:
                print(f"     海拔: {pos['altitude']:.1f}m")


def cmd_distance(args):
    """计算两点间距离"""
    try:
        lat1 = float(args.lat1)
        lon1 = float(args.lon1)
        lat2 = float(args.lat2)
        lon2 = float(args.lon2)
        
        calculator = GPSCalculator()
        distance = calculator.haversine_distance(lat1, lon1, lat2, lon2, args.unit)
        
        print(f"\n起点: ({lat1:.6f}, {lon1:.6f})")
        print(f"终点: ({lat2:.6f}, {lon2:.6f})")
        print(f"距离: {distance:.2f} {args.unit}")
        
    except ValueError:
        print("错误：请输入有效的数值")
        sys.exit(1)


def cmd_bearing(args):
    """计算方位角"""
    try:
        lat1 = float(args.lat1)
        lon1 = float(args.lon1)
        lat2 = float(args.lat2)
        lon2 = float(args.lon2)
        
        calculator = GPSCalculator()
        bearing = calculator.bearing(lat1, lon1, lat2, lon2)
        
        print(f"\n起点: ({lat1:.6f}, {lon1:.6f})")
        print(f"终点: ({lat2:.6f}, {lon2:.6f})")
        print(f"方位角: {bearing:.1f}°")
        
    except ValueError:
        print("错误：请输入有效的数值")
        sys.exit(1)


def cmd_export(args):
    """导出 KML 文件"""
    if not os.path.exists(args.file):
        print(f"错误：文件 {args.file} 不存在")
        sys.exit(1)
    
    parser = NMEAParser()
    sentences = parser.parse_file(args.file)
    positions = parser.get_positions(sentences)
    
    if not positions:
        print("错误：文件中没有有效的 GPS 位置数据")
        sys.exit(1)
    
    # 提取轨迹点
    points = [(p['latitude'], p['longitude']) for p in positions]
    
    exporter = KMLExporter()
    exporter.add_track(points, name=args.name, color=args.color)
    
    if exporter.save(args.output):
        print(f"\n成功导出 KML 文件:")
        print(f"  输出文件: {args.output}")
        print(f"  轨迹名称: {args.name}")
        print(f"  轨迹点数: {len(points)}")
    else:
        print("错误：导出 KML 文件失败")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='GPS NMEA 解析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 解析 NMEA 文件
  python cli.py parse sample_data/sample.nmea
  
  # 计算距离（北京到上海）
  python cli.py distance --lat1 39.9042 --lon1 116.4074 --lat2 31.2304 --lon2 121.4737
  
  # 计算方位角
  python cli.py bearing --lat1 39.9042 --lon1 116.4074 --lat2 31.2304 --lon2 121.4737
  
  # 导出 KML
  python cli.py export sample_data/sample.nmea output/trajectory.kml
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # parse 命令
    parse_parser = subparsers.add_parser('parse', help='解析 NMEA 文件')
    parse_parser.add_argument('file', help='NMEA 文件路径')
    parse_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # distance 命令
    distance_parser = subparsers.add_parser('distance', help='计算两点间距离')
    distance_parser.add_argument('--lat1', required=True, help='起点纬度')
    distance_parser.add_argument('--lon1', required=True, help='起点经度')
    distance_parser.add_argument('--lat2', required=True, help='终点纬度')
    distance_parser.add_argument('--lon2', required=True, help='终点经度')
    distance_parser.add_argument('--unit', choices=['km', 'nm', 'miles'], default='km',
                                 help='距离单位（默认: km）')
    
    # bearing 命令
    bearing_parser = subparsers.add_parser('bearing', help='计算方位角')
    bearing_parser.add_argument('--lat1', required=True, help='起点纬度')
    bearing_parser.add_argument('--lon1', required=True, help='起点经度')
    bearing_parser.add_argument('--lat2', required=True, help='终点纬度')
    bearing_parser.add_argument('--lon2', required=True, help='终点经度')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出 KML 文件')
    export_parser.add_argument('file', help='NMEA 文件路径')
    export_parser.add_argument('output', help='KML 输出文件路径')
    export_parser.add_argument('--name', default='GPS Track', help='轨迹名称')
    export_parser.add_argument('--color', default='ff0000ff', help='线条颜色（KML格式）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # 执行对应命令
    if args.command == 'parse':
        cmd_parse(args)
    elif args.command == 'distance':
        cmd_distance(args)
    elif args.command == 'bearing':
        cmd_bearing(args)
    elif args.command == 'export':
        cmd_export(args)


if __name__ == "__main__":
    main()
