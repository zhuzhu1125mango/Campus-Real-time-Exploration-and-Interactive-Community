"""学校论坛板块相关服务。"""

from typing import Tuple

from forum.models import Board, Category
from schools.models import School


CATEGORY_NAME = '院校专区'
CATEGORY_DEFAULTS = {
    'description': '各高校的讨论板块',
    'icon': 'el-icon-school',
    'order': 100,
}


def get_or_create_school_board(school: School) -> Tuple[Board, bool]:
    """
    获取或创建指定学校的论坛板块。

    Returns:
        (board, created): 板块对象及是否新创建。
    """
    category, _ = Category.objects.get_or_create(
        name=CATEGORY_NAME,
        defaults=CATEGORY_DEFAULTS,
    )

    board, created = Board.objects.get_or_create(
        school=school,
        defaults={
            'name': f'{school.name}论坛',
            'description': f'欢迎来到{school.name}论坛，这里是校友交流、分享资讯的地方。',
            'category': category,
            'icon': 'el-icon-school',
            'order': 0,
        },
    )
    return board, created
