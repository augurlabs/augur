# coding: utf-8
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
    Sequence
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.associationproxy import association_proxy

from augur.application.db.models.base import Base

metadata = Base.metadata


class SpdxAnnotationType(Base):
    __tablename__ = "annotation_types"
    __table_args__ = {"schema": "spdx"}

    annotation_type_id = Column(
        Integer,
        Sequence("annotation_types_annotation_type_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.annotation_types_annotation_type_id_seq'::regclass)"
        ),
        primary_key=True
    )
    name = Column(String(255), nullable=False, unique=True)


class SpdxAugurRepoMap(Base):
    __tablename__ = "augur_repo_map"
    __table_args__ = {"schema": "spdx"}

    map_id = Column(
        Integer,
        Sequence("augur_repo_map_map_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.augur_repo_map_map_id_seq'::regclass)"),
        primary_key=True
    )
    dosocs_pkg_id = Column(Integer)
    dosocs_pkg_name = Column(Text)
    repo_id = Column(Integer)
    repo_path = Column(Text)


class SpdxCreatorType(Base):
    __tablename__ = "creator_types"
    __table_args__ = {"schema": "spdx"}

    creator_type_id = Column(
        Integer,
        Sequence("creator_types_creator_type_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.creator_types_creator_type_id_seq'::regclass)"
        ),
        primary_key=True
    )
    name = Column(String(255), nullable=False)


class SpdxDocumentNamespace(Base):
    __tablename__ = "document_namespaces"
    __table_args__ = {"schema": "spdx"}

    document_namespace_id = Column(
        Integer,
        Sequence("document_namespaces_document_namespace_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.document_namespaces_document_namespace_id_seq'::regclass)"
        ),
        primary_key=True
    )
    uri = Column(String(500), nullable=False, unique=True)


class SpdxFileType(Base):
    __tablename__ = "file_types"
    __table_args__ = {"schema": "spdx"}

    file_type_id = Column(Integer)
    name = Column(String(255), primary_key=True)


class SpdxFile(Base):
    __tablename__ = "files"
    __table_args__ = {"schema": "spdx"}

    file_id = Column(
        Integer,
        Sequence("files_file_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.files_file_id_seq'::regclass)"),
        primary_key=True
    )
    file_type_id = Column(Integer)
    sha256 = Column(String(64), nullable=False, unique=True)
    copyright_text = Column(Text)
    package_id = Column(Integer)
    comment = Column(Text, nullable=False)
    notice = Column(Text, nullable=False)


class SpdxLicense(Base):
    __tablename__ = "licenses"
    __table_args__ = {"schema": "spdx"}

    license_id = Column(
        Integer,
        Sequence("licenses_license_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.licenses_license_id_seq'::regclass)"),
        primary_key=True
    )
    name = Column(String(255))
    short_name = Column(String(255), nullable=False, unique=True)
    cross_reference = Column(Text, nullable=False)
    comment = Column(Text, nullable=False)
    is_spdx_official = Column(Boolean, nullable=False)


class SpdxPackage(Base):
    __tablename__ = "packages"
    __table_args__ = (
        CheckConstraint(
            "(((sha256 IS NOT NULL))::integer + ((dosocs2_dir_code IS NOT NULL))::integer) = 1"
        ),
        UniqueConstraint("verification_code", "dosocs2_dir_code"),
        {"schema": "spdx"},
    )

    package_id = Column(
        Integer,
        Sequence("packages_package_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.packages_package_id_seq'::regclass)"),
        primary_key=True
    )
    name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False)
    file_name = Column(Text, nullable=False)
    supplier_id = Column(ForeignKey("spdx.creators.creator_id"))
    originator_id = Column(ForeignKey("spdx.creators.creator_id"))
    download_location = Column(Text)
    verification_code = Column(String(64), nullable=False)
    ver_code_excluded_file_id = Column(
        ForeignKey("spdx.packages_files.package_file_id")
    )
    sha256 = Column(String(64), unique=True)
    home_page = Column(Text)
    source_info = Column(Text, nullable=False)
    concluded_license_id = Column(ForeignKey("spdx.licenses.license_id"))
    declared_license_id = Column(ForeignKey("spdx.licenses.license_id"))
    license_comment = Column(Text, nullable=False)
    copyright_text = Column(Text)
    summary = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    comment = Column(Text, nullable=False)
    dosocs2_dir_code = Column(String(64))

    concluded_license = relationship(
        "SpdxLicense", primaryjoin="SpdxPackage.concluded_license_id == SpdxLicense.license_id"
    )
    declared_license = relationship(
        "SpdxLicense", primaryjoin="SpdxPackage.declared_license_id == SpdxLicense.license_id"
    )
    originator = relationship(
        "SpdxCreator", primaryjoin="SpdxPackage.originator_id == SpdxCreator.creator_id"
    )
    supplier = relationship(
        "SpdxCreator", primaryjoin="SpdxPackage.supplier_id == SpdxCreator.creator_id"
    )
    ver_code_excluded_file = relationship(
        "SpdxPackagesFile",
        primaryjoin="SpdxPackage.ver_code_excluded_file_id == SpdxPackagesFile.package_file_id",
    )


class SpdxPackagesFile(Base):
    __tablename__ = "packages_files"
    __table_args__ = (
        UniqueConstraint("package_id", "file_name"),
        {"schema": "spdx"}
    )

    package_file_id = Column(
        Integer,
        Sequence("packages_files_package_file_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.packages_files_package_file_id_seq'::regclass)"
        ),
        primary_key=True
    )
    package_id = Column(ForeignKey("spdx.packages.package_id"), nullable=False)
    file_id = Column(ForeignKey("spdx.files.file_id"), nullable=False)
    concluded_license_id = Column(ForeignKey("spdx.licenses.license_id"))
    license_comment = Column(Text, nullable=False)
    file_name = Column(Text, nullable=False)

    concluded_license = relationship("SpdxLicense")
    file = relationship("SpdxFile")
    package = relationship(
        "SpdxPackage", primaryjoin="SpdxPackagesFile.package_id == SpdxPackage.package_id"
    )


class SpdxProject(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "spdx"}

    package_id = Column(
        Integer,
        Sequence("projects_package_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.projects_package_id_seq'::regclass)"),
        primary_key=True
    )
    name = Column(Text, nullable=False)
    homepage = Column(Text, nullable=False)
    uri = Column(Text, nullable=False)


class SpdxRelationshipType(Base):
    __tablename__ = "relationship_types"
    __table_args__ = {"schema": "spdx"}

    relationship_type_id = Column(
        Integer,
        Sequence("relationship_types_relationship_type_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.relationship_types_relationship_type_id_seq'::regclass)"
        ),
        primary_key=True
    )
    name = Column(String(255), nullable=False, unique=True)


t_sbom_scans = Table(
    "sbom_scans",
    metadata,
    Column("repo_id", Integer),
    Column("sbom_scan", JSON),
    schema="spdx",
)


class SpdxScanner(Base):
    __tablename__ = "scanners"
    __table_args__ = {"schema": "spdx"}

    scanner_id = Column(
        Integer,
        Sequence("scanners_scanner_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.scanners_scanner_id_seq'::regclass)"),
        primary_key=True
    )
    name = Column(String(255), nullable=False, unique=True)


class SpdxCreator(Base):
    __tablename__ = "creators"
    __table_args__ = {"schema": "spdx"}

    creator_id = Column(
        Integer,
        Sequence("creators_creator_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.creators_creator_id_seq'::regclass)"),
        primary_key=True
    )
    creator_type_id = Column(
        ForeignKey("spdx.creator_types.creator_type_id"), nullable=False
    )
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)

    creator_type = relationship("SpdxCreatorType")


class SpdxDocument(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "spdx"}

    document_id = Column(
        Integer,
        Sequence("documents_document_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.documents_document_id_seq'::regclass)"),
        primary_key=True
    )
    document_namespace_id = Column(
        ForeignKey("spdx.document_namespaces.document_namespace_id"),
        nullable=False,
        unique=True,
    )
    data_license_id = Column(ForeignKey("spdx.licenses.license_id"), nullable=False)
    spdx_version = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    license_list_version = Column(String(255), nullable=False)
    created_ts = Column(TIMESTAMP(True, 6), nullable=False)
    creator_comment = Column(Text, nullable=False)
    document_comment = Column(Text, nullable=False)
    package_id = Column(ForeignKey("spdx.packages.package_id"), nullable=False)

    data_license = relationship("SpdxLicense")
    document_namespace = relationship("SpdxDocumentNamespace", uselist=False)
    package = relationship("SpdxPackage")


class SpdxFileContributor(Base):
    __tablename__ = "file_contributors"
    __table_args__ = {"schema": "spdx"}

    file_contributor_id = Column(
        Integer,
        Sequence("file_contributors_file_contributor_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.file_contributors_file_contributor_id_seq'::regclass)"
        ),
        primary_key=True
    )
    file_id = Column(ForeignKey("spdx.files.file_id"), nullable=False)
    contributor = Column(Text, nullable=False)

    file = relationship("SpdxFile")


class SpdxFilesLicense(Base):
    __tablename__ = "files_licenses"
    __table_args__ = (
        UniqueConstraint("file_id", "license_id"), 
        {"schema": "spdx"}
    )

    file_license_id = Column(
        Integer,
        Sequence("files_licenses_file_license_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.files_licenses_file_license_id_seq'::regclass)"
        ),
        primary_key=True
    )
    file_id = Column(ForeignKey("spdx.files.file_id"), nullable=False)
    license_id = Column(ForeignKey("spdx.licenses.license_id"), nullable=False)
    extracted_text = Column(Text, nullable=False)

    file = relationship("SpdxFile")
    license = relationship("SpdxLicense")


class SpdxFilesScan(Base):
    __tablename__ = "files_scans"
    __table_args__ = (
        UniqueConstraint("file_id", "scanner_id"), 
        {"schema": "spdx"}
    )

    file_scan_id = Column(
        Integer,
        Sequence("files_scans_file_scan_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.files_scans_file_scan_id_seq'::regclass)"),
        primary_key=True
    )
    file_id = Column(ForeignKey("spdx.files.file_id"), nullable=False)
    scanner_id = Column(ForeignKey("spdx.scanners.scanner_id"), nullable=False)

    file = relationship("SpdxFile")
    scanner = relationship("SpdxScanner")


class SpdxPackagesScan(Base):
    __tablename__ = "packages_scans"
    __table_args__ = (
        UniqueConstraint("package_id", "scanner_id"), 
        {"schema": "spdx"}
    )

    package_scan_id = Column(
        Integer,
        Sequence("packages_scans_package_scan_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.packages_scans_package_scan_id_seq'::regclass)"
        ),
        primary_key=True
    )
    package_id = Column(ForeignKey("spdx.packages.package_id"), nullable=False)
    scanner_id = Column(ForeignKey("spdx.scanners.scanner_id"), nullable=False)

    package = relationship("SpdxPackage")
    scanner = relationship("SpdxScanner")


class SpdxDocumentsCreator(Base):
    __tablename__ = "documents_creators"
    __table_args__ = {"schema": "spdx"}

    document_creator_id = Column(
        Integer,
        Sequence("documents_creators_document_creator_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.documents_creators_document_creator_id_seq'::regclass)"
        ),
        primary_key=True
    )
    document_id = Column(ForeignKey("spdx.documents.document_id"), nullable=False)
    creator_id = Column(ForeignKey("spdx.creators.creator_id"), nullable=False)

    creator = relationship("SpdxCreator")
    document = relationship("SpdxDocument")


class SpdxExternalRef(Base):
    __tablename__ = "external_refs"
    __table_args__ = (
        UniqueConstraint("document_id", "id_string"), 
        {"schema": "spdx"}
    )

    external_ref_id = Column(
        Integer,
        Sequence("external_refs_external_ref_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.external_refs_external_ref_id_seq'::regclass)"
        ),
        primary_key=True
    )
    document_id = Column(ForeignKey("spdx.documents.document_id"), nullable=False)
    document_namespace_id = Column(
        ForeignKey("spdx.document_namespaces.document_namespace_id"), nullable=False
    )
    id_string = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=False)

    document = relationship("SpdxDocument")
    document_namespace = relationship("SpdxDocumentNamespace")


class SpdxAnnotation(Base):
    __tablename__ = "annotations"
    __table_args__ = {"schema": "spdx"}

    annotation_id = Column(
        Integer,
        Sequence("annotations_annotation_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.annotations_annotation_id_seq'::regclass)"),
        primary_key=True
    )
    document_id = Column(ForeignKey("spdx.documents.document_id"), nullable=False)
    annotation_type_id = Column(
        ForeignKey("spdx.annotation_types.annotation_type_id"), nullable=False
    )
    identifier_id = Column(ForeignKey("spdx.identifiers.identifier_id"), nullable=False)
    creator_id = Column(ForeignKey("spdx.creators.creator_id"), nullable=False)
    created_ts = Column(TIMESTAMP(True, 6))
    comment = Column(Text, nullable=False)

    annotation_type = relationship("SpdxAnnotationType")
    creator = relationship("SpdxCreator")
    document = relationship("SpdxDocument")
    identifier = relationship("SpdxIdentifier")


class SpdxRelationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint(
            "left_identifier_id", "right_identifier_id", "relationship_type_id"
        ),
        {"schema": "spdx"},
    )

    relationship_id = Column(
        Integer,
        Sequence("relationships_relationship_id_seq", start=1, schema="spdx"),
        server_default=text(
            "nextval('spdx.relationships_relationship_id_seq'::regclass)"
        ),
        primary_key=True
    )
    left_identifier_id = Column(
        ForeignKey("spdx.identifiers.identifier_id"), nullable=False
    )
    right_identifier_id = Column(
        ForeignKey("spdx.identifiers.identifier_id"), nullable=False
    )
    relationship_type_id = Column(
        ForeignKey("spdx.relationship_types.relationship_type_id"), nullable=False
    )
    relationship_comment = Column(Text, nullable=False)

    left_identifier = relationship(
        "SpdxIdentifier",
        primaryjoin="SpdxRelationship.left_identifier_id == SpdxIdentifier.identifier_id",
        backref="to_relationships",
    )
    relationship_type = relationship("SpdxRelationshipType")
    right_identifier = relationship(
        "SpdxIdentifier",
        primaryjoin="SpdxRelationship.right_identifier_id == SpdxIdentifier.identifier_id",
        backref="from_relationships",
    )


class SpdxIdentifier(Base):
    __tablename__ = "identifiers"
    __table_args__ = (
        CheckConstraint(
            "((((document_id IS NOT NULL))::integer + ((package_id IS NOT NULL))::integer) + ((package_file_id IS NOT NULL))::integer) = 1"
        ),
        UniqueConstraint("document_namespace_id", "document_id"),
        UniqueConstraint("document_namespace_id", "id_string"),
        UniqueConstraint("document_namespace_id", "package_file_id"),
        UniqueConstraint("document_namespace_id", "package_id"),
        {"schema": "spdx"},
    )

    identifier_id = Column(
        Integer,
        Sequence("identifiers_identifier_id_seq", start=1, schema="spdx"),
        server_default=text("nextval('spdx.identifiers_identifier_id_seq'::regclass)"),
        primary_key=True
    )
    document_namespace_id = Column(
        ForeignKey("spdx.document_namespaces.document_namespace_id"), nullable=False
    )
    id_string = Column(String(255), nullable=False)
    document_id = Column(ForeignKey("spdx.documents.document_id"))
    package_id = Column(ForeignKey("spdx.packages.package_id"))
    package_file_id = Column(ForeignKey("spdx.packages_files.package_file_id"))

    document = relationship("SpdxDocument")
    document_namespace = relationship("SpdxDocumentNamespace")
    package_file = relationship("SpdxPackagesFile")
    package = relationship("SpdxPackage")

    to_identifiers = association_proxy("to_relationships", "right_identifier")
    from_identifiers = association_proxy("from_relationships", "left_identifier")
