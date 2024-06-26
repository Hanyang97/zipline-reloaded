import sqlalchemy as sa

# Define a version number for the database generated by these writers
# Increment this version number any time a change is made to the schema of the
# assets database
# NOTE: When upgrading this remember to add a downgrade in:
# .asset_db_migrations
ASSET_DB_VERSION = 7

# A frozenset of the names of all tables in the assets db
# NOTE: When modifying this schema, update the ASSET_DB_VERSION value
asset_db_table_names = frozenset(
    {
        "asset_router",
        "equities",
        "equity_symbol_mappings",
        "equity_supplementary_mappings",
        "futures_contracts",
        "exchanges",
        "futures_root_symbols",
        "version_info",
    }
)

metadata = sa.MetaData()

exchanges = sa.Table(
    "exchanges",
    metadata,
    sa.Column(
        "exchange",
        sa.Text,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column("canonical_name", sa.Text, nullable=False),
    sa.Column("country_code", sa.Text, nullable=False),
)

equities = sa.Table(
    "equities",
    metadata,
    sa.Column(
        "sid",
        sa.BigInteger,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column("asset_name", sa.Text),
    sa.Column("start_date", sa.BigInteger, default=0, nullable=False),
    sa.Column("end_date", sa.BigInteger, nullable=False),
    sa.Column("first_traded", sa.BigInteger),
    sa.Column("auto_close_date", sa.BigInteger),
    sa.Column("exchange", sa.Text, sa.ForeignKey(exchanges.c.exchange)),
)

equity_symbol_mappings = sa.Table(
    "equity_symbol_mappings",
    metadata,
    sa.Column(
        "id",
        sa.BigInteger,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        "sid",
        sa.BigInteger,
        sa.ForeignKey(equities.c.sid),
        nullable=False,
        index=True,
    ),
    sa.Column(
        "symbol",
        sa.Text,
        nullable=False,
    ),
    sa.Column(
        "company_symbol",
        sa.Text,
        index=True,
    ),
    sa.Column(
        "share_class_symbol",
        sa.Text,
    ),
    sa.Column(
        "start_date",
        sa.BigInteger,
        nullable=False,
    ),
    sa.Column(
        "end_date",
        sa.BigInteger,
        nullable=False,
    ),
)

equity_supplementary_mappings = sa.Table(
    "equity_supplementary_mappings",
    metadata,
    sa.Column(
        "sid",
        sa.BigInteger,
        sa.ForeignKey(equities.c.sid),
        nullable=False,
        primary_key=True,
    ),
    sa.Column("field", sa.Text, nullable=False, primary_key=True),
    sa.Column("start_date", sa.BigInteger, nullable=False, primary_key=True),
    sa.Column("end_date", sa.BigInteger, nullable=False),
    sa.Column("value", sa.Text, nullable=False),
)

futures_root_symbols = sa.Table(
    "futures_root_symbols",
    metadata,
    sa.Column(
        "root_symbol",
        sa.Text,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column("root_symbol_id", sa.BigInteger),
    sa.Column("sector", sa.Text),
    sa.Column("description", sa.Text),
    sa.Column(
        "exchange",
        sa.Text,
        sa.ForeignKey(exchanges.c.exchange),
    ),
)

futures_contracts = sa.Table(
    "futures_contracts",
    metadata,
    sa.Column(
        "sid",
        sa.BigInteger,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column("symbol", sa.Text, unique=True, index=True),
    sa.Column(
        "root_symbol",
        sa.Text,
        sa.ForeignKey(futures_root_symbols.c.root_symbol),
        index=True,
    ),
    sa.Column("asset_name", sa.Text),
    sa.Column("start_date", sa.BigInteger, default=0, nullable=False),
    sa.Column("end_date", sa.BigInteger, nullable=False),
    sa.Column("first_traded", sa.BigInteger),
    sa.Column(
        "exchange",
        sa.Text,
        sa.ForeignKey(exchanges.c.exchange),
    ),
    sa.Column("notice_date", sa.BigInteger, nullable=False),
    sa.Column("expiration_date", sa.BigInteger, nullable=False),
    sa.Column("auto_close_date", sa.BigInteger, nullable=False),
    sa.Column("multiplier", sa.Float),
    sa.Column("tick_size", sa.Float),
)

asset_router = sa.Table(
    "asset_router",
    metadata,
    sa.Column("sid", sa.BigInteger, unique=True, nullable=False, primary_key=True),
    sa.Column("asset_type", sa.Text),
)

version_info = sa.Table(
    "version_info",
    metadata,
    sa.Column(
        "id",
        sa.Integer,
        unique=True,
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        "version",
        sa.Integer,
        unique=True,
        nullable=False,
    ),
    # This constraint ensures a single entry in this table
    sa.CheckConstraint("id <= 1"),
)
