from django.db import models
import markdown

# Create your models here.

# 用户表
class User(models.Model):
    user_id = models.BigAutoField(primary_key = True)

    name = models.CharField(max_length = 40)
    nickname = models.CharField(max_length = 40)
    password = models.CharField(max_length = 32)
    regist_time = models.DateTimeField()
    email = models.EmailField(null = True, blank = True)
    description = models.CharField(max_length = 100, null = True, blank = True)

    avatar = models.CharField(null= True,max_length= 100, default="https://raw.githubusercontent.com/oi-songer/oi-songer.github.io/master/portal.jpg")

    class Meta:
        db_table = 'User'

# 分类表
class Category(models.Model):
    cate_id = models.BigAutoField(primary_key = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE)
    cate_name = models.CharField(max_length = 40)

    class Meta:
        db_table = 'Category'

# 博客内容表
class Blog(models.Model):
    blog_id = models.BigAutoField(primary_key = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE )
    cate = models.ForeignKey(Category, on_delete = models.CASCADE )
    content = models.TextField()
    title = models.CharField(max_length = 100)
    view_num = models.IntegerField()
    like_num = models.IntegerField()
    create_time = models.DateTimeField()
    modified_time = models.DateTimeField()

    # 将数据库里存储的markdown代码转化为HTML
    def toHTML(self):
        return markdown.markdown(self.content.__str__(),
            extensions=[
            # 包含 缩写、表格等常用扩展
            'markdown.extensions.extra',
            # 语法高亮扩展
            'markdown.extensions.codehilite',
            ])

    # 返回博客的Preview部分，使用HTML格式
    def preview(self):
        str = self.content.__str__()
        if (str.find("<!--more-->")):
            str = markdown.markdown(str[0:str.index("<!--more-->")],
                extensions=[
                # 包含 缩写、表格等常用扩展
                'markdown.extensions.extra',
                # 语法高亮扩展
                'markdown.extensions.codehilite',
                ])
        else:
            str = "无预览"
        return str

    class Meta:
        db_table = 'Blog'

# 评论表
class Comment(models.Model):
    comment_id = models.BigAutoField(primary_key = True)

    blog = models.ForeignKey(Blog, on_delete = models.CASCADE )
    user = models.ForeignKey(User, on_delete = models.CASCADE )
    content = models.CharField(max_length = 600)
    time = models.DateTimeField()

    class Meta:
        db_table = 'Comment'

# 标签表
class Tag(models.Model):
    tag_id = models.BigAutoField(primary_key = True)

    tag_name = models.CharField(max_length = 40)

    class Meta:
        db_table = 'Tag'

# 博客-标签表
class BlogTag(models.Model):
    blog_tag_id = models.BigAutoField(primary_key = True)

    blog = models.ForeignKey(Blog, on_delete = models.CASCADE )
    tag = models.ForeignKey(Tag, on_delete = models.CASCADE )

    class Meta:
        db_table = 'BlogTag'



# 收藏夹表
class Favourite(models.Model):
    favourite_id = models.BigAutoField(primary_key = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE )
    blog = models.ForeignKey(Blog, on_delete = models.CASCADE )

    class Meta:
        db_table = 'Favourite'

# 关注表
class Follow(models.Model):
    follow_id = models.BigAutoField(primary_key = True)

    # 由于两个外键都指向了User，所以需要设置related_name
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'follows' )
    fld_user = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'followers' )

    class Meta:
        db_table = 'Follow'

# 通知表
class Notification(models.Model):
    noti_id = models.BigAutoField(primary_key = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE )
    content = models.CharField(max_length = 400)
    unread = models.BooleanField(default = True)

    class Meta:
        db_table = 'Notification'

# Cookie表
class Cookie(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE )
    cookie = models.CharField(max_length = 20)

    class Meta:
        db_table = 'Cookie'
