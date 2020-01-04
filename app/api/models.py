import string

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from polymorphic.models import PolymorphicModel

from .managers import AnnotationManager, Seq2seqAnnotationManager

DOCUMENT_CLASSIFICATION = 'DocumentClassification'
SEQUENCE_LABELING = 'SequenceLabeling'
SEQ2SEQ = 'Seq2seq'
PROJECT_CHOICES = (
    (DOCUMENT_CLASSIFICATION, 'document classification'),
    (SEQUENCE_LABELING, 'sequence labeling'),
    (SEQ2SEQ, 'sequence to sequence'),
)


class Project(PolymorphicModel):
    name = models.CharField(max_length=100)
    description = models.TextField(default='')
    guideline = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, related_name='projects')
    project_type = models.CharField(max_length=30, choices=PROJECT_CHOICES)
    randomize_document_order = models.BooleanField(default=False)
    collaborative_annotation = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('upload', args=[self.id])

    @property
    def image(self):
        raise NotImplementedError()

    def get_bundle_name(self):
        raise NotImplementedError()

    def get_bundle_name_upload(self):
        raise NotImplementedError()

    def get_bundle_name_download(self):
        raise NotImplementedError()

    def get_annotation_serializer(self):
        raise NotImplementedError()

    def get_annotation_class(self):
        raise NotImplementedError()

    def get_storage(self, data):
        raise NotImplementedError()

    def __str__(self):
        return self.name


class TextClassificationProject(Project):

    @property
    def image(self):
        return staticfiles_storage.url('assets/images/cats/text_classification.jpg')

    def get_bundle_name(self):
        return 'document_classification'

    def get_bundle_name_upload(self):
        return 'upload_text_classification'

    def get_bundle_name_download(self):
        return 'download_text_classification'

    def get_annotation_serializer(self):
        from .serializers import DocumentAnnotationSerializer
        return DocumentAnnotationSerializer

    def get_annotation_class(self):
        return DocumentAnnotation

    def get_storage(self, data):
        from .utils import ClassificationStorage
        return ClassificationStorage(data, self)


class SequenceLabelingProject(Project):

    @property
    def image(self):
        return staticfiles_storage.url('assets/images/cats/sequence_labeling.jpg')

    def get_bundle_name(self):
        return 'sequence_labeling'

    def get_bundle_name_upload(self):
        return 'upload_sequence_labeling'

    def get_bundle_name_download(self):
        return 'download_sequence_labeling'

    def get_annotation_serializer(self):
        from .serializers import SequenceAnnotationSerializer
        return SequenceAnnotationSerializer

    def get_annotation_class(self):
        return SequenceAnnotation

    def get_storage(self, data):
        from .utils import SequenceLabelingStorage
        return SequenceLabelingStorage(data, self)


class Seq2seqProject(Project):

    @property
    def image(self):
        return staticfiles_storage.url('assets/images/cats/seq2seq.jpg')

    def get_bundle_name(self):
        return 'seq2seq'

    def get_bundle_name_upload(self):
        return 'upload_seq2seq'

    def get_bundle_name_download(self):
        return 'download_seq2seq'

    def get_annotation_serializer(self):
        from .serializers import Seq2seqAnnotationSerializer
        return Seq2seqAnnotationSerializer

    def get_annotation_class(self):
        return Seq2seqAnnotation

    def get_storage(self, data):
        from .utils import Seq2seqStorage
        return Seq2seqStorage(data, self)


class Label(models.Model):
    PREFIX_KEYS = (
        ('ctrl', 'ctrl'),
        ('shift', 'shift'),
        ('ctrl shift', 'ctrl shift')
    )
    SUFFIX_KEYS = tuple(
        (c, c) for c in string.ascii_lowercase
    )

    text = models.CharField(max_length=100)
    prefix_key = models.CharField(max_length=10, blank=True, null=True, choices=PREFIX_KEYS)
    suffix_key = models.CharField(max_length=1, blank=True, null=True, choices=SUFFIX_KEYS)
    project = models.ForeignKey(Project, related_name='labels', on_delete=models.CASCADE)
    background_color = models.CharField(max_length=7, default='#209cee')
    text_color = models.CharField(max_length=7, default='#ffffff')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text

    def clean(self):
        # Don't allow shortcut key not to have a suffix key.
        if self.prefix_key and not self.suffix_key:
            raise ValidationError('Shortcut key may not have a suffix key.')

        # each shortcut (prefix key + suffix key) can only be assigned to one label
        if self.suffix_key or self.prefix_key:
            other_labels = self.project.labels.exclude(id=self.id)
            if other_labels.filter(suffix_key=self.suffix_key, prefix_key=self.prefix_key).exists():
                raise ValidationError('A label with this shortcut already exists in the project')

        super().clean()

    class Meta:
        unique_together = (
            ('project', 'text'),
        )


class Paper(models.Model):
    abstract = models.TextField(null=True)
    authors = models.TextField(null=True)
    doi = models.CharField(max_length=255, null=True, db_index=True)
    pmid = models.IntegerField(primary_key=True, db_index=True)
    title = models.TextField(db_index=True)
    journal = models.CharField(max_length=255, db_index=True)
    mesh_terms = models.TextField(null=True)
    publication_types = models.TextField(null=True)
    chemical_list = models.TextField(null=True)
    references = models.TextField(null=True)
    delete = models.BooleanField(default=False)
    affiliations = models.TextField(null=True)
    pmc = models.CharField(max_length=32, null=True, db_index=True)
    country = models.CharField(max_length=255, null=True)
    medline_ta = models.CharField(max_length=128, null=True)
    nlm_unique_id = models.CharField(max_length=16, null=True)
    issn_linking = models.CharField(max_length=255, null=True)
    other_id = models.CharField(max_length=255, null=True)
    keywords = models.TextField(null=True)
    pubdate = models.CharField(max_length=32, null=True)

    def __str__(self):
        return str(self.pmid)

    class Meta:
        ordering = ('pmid', )


class FullPaper(models.Model):
    """
    In the future, we need the full paper from pmc.
    """
    # For images, full paper, tables, references
    # TODO: don't we need a references? we can use pmid as an index to a paper record.
    pmc = models.CharField(max_length=32)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    full_paper = models.TextField()
    pmid_cited = models.TextField()
    doi_cited = models.TextField()
    references = models.TextField()  # Store json as text for future, more details on https://github.com/titipata/pubmed_parser#parse-pubmed-oa-citation-references
    images = models.TextField()  # Store json as text for future, more details on https://github.com/titipata/pubmed_parser#parse-pubmed-oa-images-and-captions
    tables = models.TextField()  # Store json as text for future, more details on https://github.com/titipata/pubmed_parser#parse-pubmed-oa-table-wip


class Knowledge(models.Model):
    LANG_CHOICES = (
        ('English', 'English'),
        ('Chinese', 'Chinese')
    )

    STATUS_CHOICES = (
        ('Checked', 'Checked'),  # 已审核
        ('Submitted', 'Submitted'),  # 已提交
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    language = models.CharField(max_length=16, choices=LANG_CHOICES, default='English')
    title = models.TextField()
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, null=True)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tags = models.CharField(max_length=255)
    liked_num = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='Submitted')

    def __str__(self):
        return str(self.id)

    class Meta:
        # Each author can only have one version for a paper.
        unique_together = ('author', 'paper', 'language')


class Document(models.Model):
    TYPE_CHOICES = (
        ('Custom', 'Custom'),
        ('Knowledge', 'Knowledge'),
        ('Paper', 'Paper'),
        ('Case', 'Case')
    )

    text = models.TextField()
    project = models.ForeignKey(Project, related_name='documents', on_delete=models.CASCADE)
    meta = models.TextField(default='{}')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reference_id = models.CharField(max_length=8, null=True)
    reference_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default='Custom', null=True)
    annotations_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.text[:50]


class Annotation(models.Model):
    objects = AnnotationManager()

    prob = models.FloatField(default=0.0)
    manual = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class DocumentAnnotation(Annotation):
    document = models.ForeignKey(Document, related_name='doc_annotations', on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('document', 'user', 'label')


class SequenceAnnotation(Annotation):
    document = models.ForeignKey(Document, related_name='seq_annotations', on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    start_offset = models.IntegerField()
    end_offset = models.IntegerField()

    def clean(self):
        if self.start_offset >= self.end_offset:
            raise ValidationError('start_offset is after end_offset')

    class Meta:
        unique_together = ('document', 'user', 'label', 'start_offset', 'end_offset')


class Seq2seqAnnotation(Annotation):
    # Override AnnotationManager for custom functionality
    objects = Seq2seqAnnotationManager()

    document = models.ForeignKey(Document, related_name='seq2seq_annotations', on_delete=models.CASCADE)
    text = models.CharField(max_length=500)

    class Meta:
        unique_together = ('document', 'user', 'text')


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RoleMapping(models.Model):
    user = models.ForeignKey(User, related_name='role_mappings', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name='role_mappings', on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        other_rolemappings = self.project.role_mappings.exclude(id=self.id)

        if other_rolemappings.filter(user=self.user, project=self.project).exists():
            raise ValidationError('This user is already assigned to a role in this project.')

    class Meta:
        unique_together = ("user", "project", "role")


@receiver(post_save, sender=RoleMapping)
def add_linked_project(sender, instance, created, **kwargs):
    if not created:
        return
    userInstance = instance.user
    projectInstance = instance.project
    if userInstance and projectInstance:
        user = User.objects.get(pk=userInstance.pk)
        project = Project.objects.get(pk=projectInstance.pk)
        user.projects.add(project)
        user.save()


@receiver(post_save)
def add_superusers_to_project(sender, instance, created, **kwargs):
    if not created:
        return
    if sender not in Project.__subclasses__():
        return
    superusers = User.objects.filter(is_superuser=True)
    admin_role = Role.objects.filter(name=settings.ROLE_PROJECT_ADMIN).first()
    if superusers and admin_role:
        RoleMapping.objects.bulk_create(
            [RoleMapping(role_id=admin_role.id, user_id=superuser.id, project_id=instance.id)
             for superuser in superusers]
        )


@receiver(post_save, sender=User)
def add_new_superuser_to_projects(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        admin_role = Role.objects.filter(name=settings.ROLE_PROJECT_ADMIN).first()
        projects = Project.objects.all()
        if admin_role and projects:
            RoleMapping.objects.bulk_create(
                [RoleMapping(role_id=admin_role.id, user_id=instance.id, project_id=project.id)
                 for project in projects]
            )


@receiver(pre_delete, sender=RoleMapping)
def delete_linked_project(sender, instance, using, **kwargs):
    userInstance = instance.user
    projectInstance = instance.project
    if userInstance and projectInstance:
        user = User.objects.get(pk=userInstance.pk)
        project = Project.objects.get(pk=projectInstance.pk)
        user.projects.remove(project)
        user.save()
