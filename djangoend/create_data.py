from django.contrib.auth import get_user_model
from forum.models import Category, Board, Topic, Post
import random

User = get_user_model()

# 创建用户
def create_users():
    users = {}
    
    # 学生用户
    student1, _ = User.objects.get_or_create(
        username='student1',
        defaults={'email': 'student1@example.com', 'bio': '计算机科学专业学生'}
    )
    student1.set_password('password123')
    student1.save()
    users['student'] = student1
    
    # 教授用户
    professor1, _ = User.objects.get_or_create(
        username='professor1',
        defaults={'email': 'professor1@example.com', 'bio': '计算机系教授'}
    )
    professor1.set_password('password123')
    professor1.save()
    users['professor'] = professor1
    
    # 校友用户
    alumni1, _ = User.objects.get_or_create(
        username='alumni1',
        defaults={'email': 'alumni1@example.com', 'bio': '2020届毕业生'}
    )
    alumni1.set_password('password123')
    alumni1.save()
    users['alumni'] = alumni1
    
    return users

# 创建论坛版块
def create_boards():
    boards = {}
    
    # 先创建分类
    category, _ = Category.objects.get_or_create(name='默认分类')
    
    board_names = ['学术交流', '校园活动', '就业信息', '技术讨论']
    for name in board_names:
        board, _ = Board.objects.get_or_create(
            name=name,
            defaults={'category': category}
        )
        boards[name] = board
    
    return boards

# 创建帖子
def create_posts(users, boards):
    # 学生帖子
    student_posts = [
        ('求推荐Python学习资源', '最近开始学习Python，有什么好的学习资源推荐吗？', '学术交流'),
        ('有人参加过编程比赛吗？', '想了解一下编程比赛的经验和准备方法', '技术讨论'),
    ]
    
    # 教授帖子
    professor_posts = [
        ('人工智能最新研究进展', '最近人工智能领域有一些重要的研究突破', '学术交流'),
        ('关于毕业论文的写作建议', '临近毕业季，给大家一些关于毕业论文写作的建议', '学术交流'),
    ]
    
    # 校友帖子
    alumni_posts = [
        ('工作后的一些感悟', '离开学校工作已经一年了，想分享一些工作后的感悟', '校园活动'),
        ('公司招聘信息', '我们公司正在招聘实习生，有兴趣的学弟学妹可以投递简历', '就业信息'),
    ]
    
    # 生成帖子
    post_data = {
        'student': student_posts,
        'professor': professor_posts,
        'alumni': alumni_posts,
    }
    
    for role, posts in post_data.items():
        if role in users:
            user = users[role]
            for title, content, board_name in posts:
                board = boards.get(board_name)
                if board:
                    # 创建主题
                    topic = Topic.objects.create(title=title, board=board, author=user)
                    # 创建首贴
                    Post.objects.create(topic=topic, author=user, content=content, is_first_post=True)
                    # 添加回复
                    for i in range(2):
                        # 随机选择其他用户作为回复者
                        reply_users = [u for r, u in users.items() if r != role]
                        if reply_users:
                            reply_user = random.choice(reply_users)
                            Post.objects.create(
                                topic=topic,
                                author=reply_user,
                                content='这个问题很有意思，我也想了解一下。',
                                is_first_post=False
                            )

# 主函数
def main():
    print("创建用户...")
    users = create_users()
    print(f"创建了 {len(users)} 个用户")
    
    print("创建论坛版块...")
    boards = create_boards()
    print(f"创建了 {len(boards)} 个论坛版块")
    
    print("生成论坛帖子...")
    create_posts(users, boards)
    print("帖子生成完成")

if __name__ == "__main__":
    main()
