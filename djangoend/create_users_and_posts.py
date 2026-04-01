import os
import django
from django.contrib.auth import get_user_model
from forum.models import Board, Topic, Post
from schools.models import School
import random
from faker import Faker

# 初始化Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

User = get_user_model()
fake = Faker('zh_CN')

# 创建用户角色
def create_users():
    # 定义不同角色的用户
    user_roles = [
        {'username': 'student1', 'email': 'student1@example.com', 'password': 'password123', 'role': 'student', 'description': '计算机科学专业学生，热爱编程和技术交流'},
        {'username': 'student2', 'email': 'student2@example.com', 'password': 'password123', 'role': 'student', 'description': '金融学专业学生，关注校园活动和就业信息'},
        {'username': 'professor1', 'email': 'professor1@example.com', 'password': 'password123', 'role': 'professor', 'description': '计算机系教授，研究人工智能和机器学习'},
        {'username': 'professor2', 'email': 'professor2@example.com', 'password': 'password123', 'role': 'professor', 'description': '经济系教授，研究金融市场和投资策略'},
        {'username': 'alumni1', 'email': 'alumni1@example.com', 'password': 'password123', 'role': 'alumni', 'description': '2020届毕业生，现任科技公司工程师'},
        {'username': 'alumni2', 'email': 'alumni2@example.com', 'password': 'password123', 'role': 'alumni', 'description': '2018届毕业生，现任金融分析师'},
        {'username': 'staff1', 'email': 'staff1@example.com', 'password': 'password123', 'role': 'staff', 'description': '学生事务处工作人员，负责校园活动组织'},
    ]
    
    users = {}
    for user_data in user_roles:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'password': user_data['password'],
                'bio': user_data['description']
            }
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
        users[user_data['role']] = user
    return users

# 创建论坛版块
def create_boards():
    boards = [
        {'name': '学术交流', 'description': '讨论学术问题，分享学习资料'},
        {'name': '校园活动', 'description': '校园活动信息发布和讨论'},
        {'name': '就业信息', 'description': '招聘信息和就业经验分享'},
        {'name': '生活分享', 'description': '校园生活和个人经验分享'},
        {'name': '技术讨论', 'description': '技术相关话题讨论'},
        {'name': '资源共享', 'description': '学习资料和资源共享'},
    ]
    
    board_objects = {}
    for board_data in boards:
        board, created = Board.objects.get_or_create(
            name=board_data['name'],
            defaults={'description': board_data['description']}
        )
        board_objects[board_data['name']] = board
    return board_objects

# 为每个角色生成帖子
def create_posts(users, boards):
    # 学生帖子
    student_posts = [
        {'title': '求推荐Python学习资源', 'content': '最近开始学习Python，有什么好的学习资源推荐吗？特别是关于数据分析的部分。', 'board': '学术交流'},
        {'title': '有人参加过编程比赛吗？', 'content': '想了解一下编程比赛的经验和准备方法，有参加过的同学分享一下吗？', 'board': '技术讨论'},
        {'title': '校园招聘会什么时候开始？', 'content': '请问今年的校园招聘会什么时候开始？有哪些公司会来？', 'board': '就业信息'},
        {'title': '分享一下我的考研复习计划', 'content': '经过一段时间的准备，我制定了一份考研复习计划，希望对大家有所帮助...', 'board': '学术交流'},
    ]
    
    # 教授帖子
    professor_posts = [
        {'title': '人工智能最新研究进展', 'content': '最近人工智能领域有一些重要的研究突破，我来分享一下我的见解...', 'board': '学术交流'},
        {'title': '关于毕业论文的写作建议', 'content': '临近毕业季，给大家一些关于毕业论文写作的建议...', 'board': '学术交流'},
        {'title': '实验室招新通知', 'content': '我的实验室正在招收新的研究助理，有兴趣的同学可以联系我...', 'board': '校园活动'},
    ]
    
    # 校友帖子
    alumni_posts = [
        {'title': '工作后的一些感悟', 'content': '离开学校工作已经一年了，想分享一些工作后的感悟和经验...', 'board': '生活分享'},
        {'title': '公司招聘信息', 'content': '我们公司正在招聘实习生，有兴趣的学弟学妹可以投递简历...', 'board': '就业信息'},
        {'title': '校友会活动通知', 'content': '下周末将举行校友会活动，欢迎大家参加...', 'board': '校园活动'},
    ]
    
    # 工作人员帖子
    staff_posts = [
        {'title': '校园文化节活动安排', 'content': '今年的校园文化节将于下月举行，详细安排如下...', 'board': '校园活动'},
        {'title': '关于学生社团招新', 'content': '新学年开始，各学生社团开始招新，有兴趣的同学可以关注...', 'board': '校园活动'},
        {'title': '图书馆新增资源通知', 'content': '图书馆新增了一批电子资源，包括数据库和电子书...', 'board': '资源共享'},
    ]
    
    # 生成帖子
    post_data = {
        'student': student_posts,
        'professor': professor_posts,
        'alumni': alumni_posts,
        'staff': staff_posts,
    }
    
    for role, posts in post_data.items():
        if role in users:
            user = users[role]
            for post_info in posts:
                board = boards.get(post_info['board'])
                if board:
                    # 创建主题
                    topic = Topic.objects.create(
                        title=post_info['title'],
                        board=board,
                        author=user
                    )
                    # 创建首贴
                    Post.objects.create(
                        topic=topic,
                        author=user,
                        content=post_info['content'],
                        is_first_post=True
                    )
                    # 添加一些回复
                    for i in range(random.randint(1, 3)):
                        # 随机选择其他用户作为回复者
                        reply_users = [u for r, u in users.items() if r != role]
                        if reply_users:
                            reply_user = random.choice(reply_users)
                            Post.objects.create(
                                topic=topic,
                                author=reply_user,
                                content=fake.paragraph(nb_sentences=3),
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
