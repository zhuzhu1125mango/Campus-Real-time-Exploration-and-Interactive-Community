import os
import csv
import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from schools.models import School

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '从CSV、Excel或JSON文件导入院校数据'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='导入文件的路径')
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'excel', 'json'],
            help='文件格式 (csv, excel, json)',
        )
        parser.add_argument(
            '--encoding',
            type=str,
            default='utf-8',
            help='文件编码，默认为utf-8',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='如果学校已存在，则更新学校信息',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options.get('format')
        encoding = options.get('encoding')
        update_existing = options.get('update', False)

        if not os.path.exists(file_path):
            raise CommandError(f'文件不存在: {file_path}')

        # 如果未指定格式，根据文件扩展名推断
        if not file_format:
            ext = Path(file_path).suffix.lower()
            if ext == '.csv':
                file_format = 'csv'
            elif ext in ['.xls', '.xlsx']:
                file_format = 'excel'
            elif ext == '.json':
                file_format = 'json'
            else:
                raise CommandError(f'无法从扩展名推断文件格式: {ext}，请使用--format参数指定格式')

        try:
            if file_format == 'csv':
                self.import_from_csv(file_path, encoding, update_existing)
            elif file_format == 'excel':
                self.import_from_excel(file_path, update_existing)
            elif file_format == 'json':
                self.import_from_json(file_path, encoding, update_existing)
        except Exception as e:
            raise CommandError(f'导入过程中发生错误: {str(e)}')

        self.stdout.write(self.style.SUCCESS('院校数据导入成功!'))

    def import_from_csv(self, file_path, encoding, update_existing):
        """从CSV文件导入院校数据"""
        self.stdout.write(f'从CSV文件导入数据: {file_path}')
        
        self.created_count = 0
        self.updated_count = 0
        self.error_count = 0

        try:
            with open(file_path, 'r', encoding=encoding) as csv_file:
                reader = csv.DictReader(csv_file)
                
                with transaction.atomic():
                    for row in reader:
                        try:
                            self._process_school_data(row, update_existing)
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"处理学校数据时出错: {str(e)}, 数据: {row}")
                            if self.error_count > 10:  # 如果错误过多，终止导入
                                raise CommandError(f"导入过程中错误过多，已终止导入。")
        except UnicodeDecodeError:
            raise CommandError(f"无法以 {encoding} 编码读取CSV文件，请尝试不同的编码，例如 'gbk', 'gb2312', 'utf-8-sig'等")

        self.stdout.write(f"创建了 {self.created_count} 所学校，更新了 {self.updated_count} 所学校，遇到 {self.error_count} 个错误。")

    def import_from_excel(self, file_path, update_existing):
        """从Excel文件导入院校数据"""
        self.stdout.write(f'从Excel文件导入数据: {file_path}')
        
        try:
            import pandas as pd
        except ImportError:
            raise CommandError("缺少pandas库，请使用'pip install pandas openpyxl'安装")

        self.created_count = 0
        self.updated_count = 0
        self.error_count = 0

        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            # 转换列名为小写
            df.columns = [col.lower() for col in df.columns]
            
            with transaction.atomic():
                for _, row in df.iterrows():
                    try:
                        # 将pandas系列转换为字典
                        data = row.to_dict()
                        # 处理NaN值
                        for key, value in data.items():
                            if pd.isna(value):
                                data[key] = None
                        
                        self._process_school_data(data, update_existing)
                    except Exception as e:
                        self.error_count += 1
                        logger.error(f"处理学校数据时出错: {str(e)}, 数据: {row.to_dict()}")
                        if self.error_count > 10:  # 如果错误过多，终止导入
                            raise CommandError(f"导入过程中错误过多，已终止导入。")
        except Exception as e:
            raise CommandError(f"读取Excel文件失败: {str(e)}")

        self.stdout.write(f"创建了 {self.created_count} 所学校，更新了 {self.updated_count} 所学校，遇到 {self.error_count} 个错误。")

    def import_from_json(self, file_path, encoding, update_existing):
        """从JSON文件导入院校数据"""
        self.stdout.write(f'从JSON文件导入数据: {file_path}')
        
        self.created_count = 0
        self.updated_count = 0
        self.error_count = 0

        try:
            with open(file_path, 'r', encoding=encoding) as json_file:
                data = json.load(json_file)
                
                # 检查是否是包含多个学校的列表
                if isinstance(data, list):
                    schools_data = data
                # 或者是包含学校列表的字典
                elif isinstance(data, dict) and 'schools' in data:
                    schools_data = data['schools']
                else:
                    # 假设是单个学校的数据
                    schools_data = [data]
                
                with transaction.atomic():
                    for school_data in schools_data:
                        try:
                            self._process_school_data(school_data, update_existing)
                        except Exception as e:
                            self.error_count += 1
                            logger.error(f"处理学校数据时出错: {str(e)}, 数据: {school_data}")
                            if self.error_count > 10:  # 如果错误过多，终止导入
                                raise CommandError(f"导入过程中错误过多，已终止导入。")
        except json.JSONDecodeError:
            raise CommandError("JSON文件格式错误")
        except UnicodeDecodeError:
            raise CommandError(f"无法以 {encoding} 编码读取JSON文件，请尝试不同的编码")

        self.stdout.write(f"创建了 {self.created_count} 所学校，更新了 {self.updated_count} 所学校，遇到 {self.error_count} 个错误。")

    def _process_school_data(self, data, update_existing):
        """处理单个学校数据"""
        # 标准化字段名
        normalized_data = self._normalize_field_names(data)
        
        # 提取必填字段 - 只要求名称字段
        if 'name' not in normalized_data or not normalized_data['name']:
            raise ValueError(f"缺少必填字段: name")
        
        # 检查学校是否已存在（优先通过代码检查，如果没有代码则通过名称检查）
        try:
            if 'code' in normalized_data:
                school = School.objects.get(code=normalized_data['code'])
            else:
                school = School.objects.get(name=normalized_data['name'])
                
            if update_existing:
                # 更新现有学校
                for key, value in normalized_data.items():
                    if hasattr(school, key) and value is not None:
                        setattr(school, key, value)
                school.save()
                self.updated_count += 1
                self.stdout.write(f"更新学校: {school.name}")
            else:
                self.stdout.write(f"学校已存在，跳过: {normalized_data['name']}")
        except School.DoesNotExist:
            # 创建新学校
            school = School(**normalized_data)
            school.save()
            self.created_count += 1
            self.stdout.write(f"创建学校: {school.name}")
    
    def _normalize_field_names(self, data):
        """标准化字段名称，处理命名差异"""
        field_mapping = {
            # 常见的字段映射，根据实际数据格式调整
            'school_name': 'name',
            'institution_name': 'name',
            'university_name': 'name',
            'college_name': 'name',
            'school': 'name',  # 添加针对当前CSV的映射
            'school_code': 'code',
            'institution_code': 'code',
            'university_code': 'code',
            'college_code': 'code',
            'english': 'english_name',
            'short_name': 'abbreviation',
            'school_type': 'school_type',
            'type': 'school_type',
            'level': 'school_level',
            'school_level': 'school_level',
            'found_year': 'founded_year',
            'foundation_year': 'founded_year',
            'established': 'founded_year',
            'student_number': 'student_count',
            'faculty_number': 'faculty_count',
            'teacher_count': 'faculty_count',
            'rank_national': 'national_rank',
            'rank_world': 'world_rank',
            'homepage': 'website',
            'url': 'website',
            'intro': 'introduction',
            'description': 'introduction',
            'verified': 'is_verified',
        }

        normalized = {}
        for key, value in data.items():
            # 转换键名为小写并去除空白
            clean_key = key.lower().strip()
            # 应用映射或使用原始键名
            normalized_key = field_mapping.get(clean_key, clean_key)
            
            # 检查是否为模型字段
            if hasattr(School, normalized_key):
                normalized[normalized_key] = value
        
        # 为缺失的必填字段提供默认值
        if 'name' in normalized and 'code' not in normalized:
            # 使用学校名称的拼音首字母或其哈希值作为代码
            import hashlib
            name_hash = hashlib.md5(normalized['name'].encode('utf-8')).hexdigest()[:8]
            normalized['code'] = f"AUTO_{name_hash}"
        
        # 如果省份和城市存在但没有完整地址，则组合它们
        if 'province' in normalized and 'city' in normalized and 'address' not in normalized:
            if 'district' in data:
                normalized['address'] = f"{normalized['province']}{normalized['city']}{data['district']}"
            else:
                normalized['address'] = f"{normalized['province']}{normalized['city']}"
        
        # 如果没有指定学校类型，默认为综合类
        if 'school_type' not in normalized:
            normalized['school_type'] = 'comprehensive'
        
        # 如果没有指定学校层次，默认为普通本科
        if 'school_level' not in normalized:
            normalized['school_level'] = 'ordinary'
            
        return normalized 