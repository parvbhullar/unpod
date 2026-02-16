from unpod.common.mixin import ChoiceEnum


class ModelBasicStatus(ChoiceEnum):
    active = "Active"
    inactive = "Inactive"
    deleted = "Deleted"


class FormInputTypes(ChoiceEnum):
    text = "Text"
    textarea = "Textarea"
    email = "Email"
    number = "Number"
    slider = "Slider"
    slider_number = "Slider with Number"
    password = "Password"
    file = "File"
    url = "Url"
    tel = "Tel"
    json = "Json"
    schema = "Schema"
    repeater = "Repeater"
    hidden = "Hidden"
    switch = "Switch"
    checkbox = "Checkbox"
    radio = "Radio"
    select = "Single Select"
    multi_select = "Multi Select"
    tags = "Tags"
    color = "Color"
    date = "Date"
    datetime = "Datetime"
    time = "Time"
    month = "Month"
    week = "Week"
    range = "Range"


class FormOptionsType(ChoiceEnum):
    static = "Static"
    api = "API"


class MediaPrivacyType(ChoiceEnum):
    public = "Public"
    private = "Private"


class StatusType(ChoiceEnum):
    active = "Active"
    inactive = "Inactive"
    deleted = "Deleted"
    archive = "Archive"


class MediaType(ChoiceEnum):
    image = "Image"
    video = "Video"
    document = "Document"
    file = "File"
    audio = "Audio"
    json = "Json"
    pdf = "Pdf"
    excel = "Excel"
    Word = "Word"
    markdown = "Markdown"
    text = "Text"
    powerpoint = "Powerpoint"
    collection = "Collection"


class MediaObjectRelation(ChoiceEnum):
    attachment = "Attachment"
    cover = "Cover"
    content = "Content"
    media = "Media"


class ObjectType(ChoiceEnum):
    post = "Post"
    thread = "Thread"
    space = "Space"
    user = "User"
    pilot = "Pilot"


class InviteType(ChoiceEnum):
    organization = "Organization"
    space = "Space"


class PrivacyType(ChoiceEnum):
    public = "Public"
    private = "Private"
    shared = "Shared"
    link = "Link"


class FileStorage(ChoiceEnum):
    cloudinary = "Cloudinary"
    s3 = "S3"
    mux = "Mux"


class MediaUploadStatus(ChoiceEnum):
    created = "Created"
    uploaded = "Uploaded"


class SizeUnit(ChoiceEnum):
    BYTES = "BYTES"
    KB = "KB"
    MB = "MB"
    GB = "GB"


class ReactionType(ChoiceEnum):
    like = "Like"
    dislike = "Dislike"
    clap = "Clap"


class PostStatus(ChoiceEnum):
    draft = "Draft"
    scheduled = "Scheduled"
    ongoing = "Ongoing"
    finished = "Finished"
    live = "Live"
    published = "Published"


class RecordingVideoStatus(ChoiceEnum):
    not_processed = "Not Processed"
    processing = "Processing"
    removed = "Removed"
    uploaded = "Uploaded"
    failed = "Failed"
    post_created = "Post Created"


class PostRelation(ChoiceEnum):
    seq_post = "Sequence Post"
    reply = "Reply"
    main_post = "Main Post"


class OrganisationAccountType(ChoiceEnum):
    individual = "Individual"
    builders = "Builders"
    startup = "Startup"
    entrepreneur = "Entrepreneur"
    investors = "Investors"
    mentors = "Mentors"
    consultants = "Consultants"
    influencers = "Influencers"
    others = "Others"


class PostType(ChoiceEnum):
    post = "Post"
    article = "Article"
    question = "Question"
    challenge = "Challenge"
    bounty = "Bounty"
    event = "Event"
    webinar = "Webinar"
    task = "Task"
    ask = "Ask"
    notebook = "Notebook"


class PostContentType(ChoiceEnum):
    text = "Text"
    video = "Video"
    audio = "Audio"
    video_stream = "Video Stream"
    audio_stream = "AudioStream"
    voice = "Voice"


class PostExtraContentType(ChoiceEnum):
    image = "Image"
    poll = "Poll"
    location = "Location"
    metric = "Metric"


class PermissionOperation(ChoiceEnum):
    add = "add"
    edit = "edit"
    delete = "Delete"
    archive = "Archive"
    share_entity = "share_entity"
    privacy_update = "privacy_update"
    view_list = "view_list"
    view_user_list = "view_user_list"
    view_detail = "view_detail"
    comment = "comment"
    use_superpilot = "use_superpilot"
    transfer_ownership = "transfer_ownership"
    start_stream = "start_stream"
    end_stream = "end_stream"


class SpaceType(ChoiceEnum):
    general = "general"
    knowledge_base = "knowledge_base"


class OrgTypes(ChoiceEnum):
    free = "Free"
    pro = "Pro"
    enterprise = "Enterprise"


class KnowledgeBaseContentType(ChoiceEnum):
    general = "general"
    document = "document"
    image = "image"
    media = "media"
    tabular = "tabular"
    email = "email"
    code = "code"
    webpage = "webpage"
    collection = "collection"
    contact = "contact"
    table = "table"
    evals = "evals"


class DataObjectStatus(ChoiceEnum):
    ready = "Ready"
    progress = "Progress"
    indexed = "Indexed"
    failed = "Failed"


class DataObjectSource(ChoiceEnum):
    imported = "imported"
    drive = "drive"
    email = "email"
    onedrive = "onedrive"
    jira = "jira"
    db = "db"


class PilotTypes(ChoiceEnum):
    Tool = "Tool"
    Connector = "Connector"
    Data = "Data"
    AI = "AI"
    LLM = "LLM"
    Pilot = "Pilot"
    Message = "Message"
    Voice = "Voice"


class PluginTypes(ChoiceEnum):
    LOADERS = "loaders"
    MODELS = "models"
    VECTOR_STORES = "vector_stores"
    PLUGINS = "plugins"


class ModelTypes(ChoiceEnum):
    EMBEDDING = "embedding"
    CHAT = "chat"
    TEXT = "text"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    CODE = "code"
    TRANSCRIBER = "transcriber"
    VOICE = "voice"


class PilotState(ChoiceEnum):
    draft = "Draft"
    published = "Published"


class RoleCodes(ChoiceEnum):
    owner = "owner"
    viewer = "viewer"
    editor = "editor"


class BlockTypes(ChoiceEnum):
    input_form = "Input Form"
    output_form = "Output Form"
    markdown = "Markdown"
    code = "Code"
    llm_model = "LLM Model"
    pilot = "Pilot"
    form = "form"
    api = "api"
    llm = "llm"
    invoice_ocr_block = "invoice_ocr_block"


class TriggerEventTypes(ChoiceEnum):
    post_created = "post_created"


class PostRepeatType(ChoiceEnum):
    never = "never"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class RelevantTagLinkType(ChoiceEnum):
    email = "Email"
    contact = "Contact"


class VoiceQualityChoices(ChoiceEnum):
    high = "High"
    good = "Good"


class VoiceGenderChoices(ChoiceEnum):
    M = "Male"
    F = "Female"


class TelephonyType(ChoiceEnum):
    sip = "sip"
    number = "number"


class TelephonyStatus(ChoiceEnum):
    active = "active"
    inactive = "inactive"


class ProviderType(ChoiceEnum):
    VOICE_INFRA = "voice_infra"
    TELEPHONY = "telephony"
    MODEL = "model"


class TelephonyNumberState(ChoiceEnum):
    ASSIGNED = "assigned"
    NOT_ASSIGNED = "not_assigned"
    CLOSED = "closed"


class TrunkDirection(ChoiceEnum):
    inbound = "inbound"
    outbound = "outbound"
    both = "both"


class TrunkType(ChoiceEnum):
    telephony = "telephony"
    voice_infra = "voice_infra"


class TrunkStatus(ChoiceEnum):
    ACTIVE = "active"
    DEACTIVE = "deactive"


class GenericStatus(ChoiceEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DRAFT = "Draft"


class GenericDocumentStatus(ChoiceEnum):
    PENDING = "Pending"
    REVIEW = "Review"
    APPROVED = "Approved"


class GenericDocumentsStatus(ChoiceEnum):
    pending = "Pending"
    review = "Review"
    approve = "Approve"


class DocumentType(ChoiceEnum):
    GST_CERTIFICATE = "GST Certificate"
    COMPANY_PAN = "Company PAN"
    INCORPORATION_CERTIFICATE = "Certificate of Incorporation"
    ID_PROOF = "ID Proof"
    CONTRACT = "Contract"
    OTHER = "Other"


class DocumentStatus(ChoiceEnum):
    review = "Review"
    reject = "Reject"
    approve = "Approve"


class OwnerType(ChoiceEnum):
    UNPOD = "unpod"
    SELF = "self"


class NumberType(ChoiceEnum):
    SIP = "sip"
    NUMBER = "number"


class ConfigType(ChoiceEnum):
    rule = "rule"
    service = "service"
    other = "other"


class ProvidersModelTypes(ChoiceEnum):
    LLM = "LLM"
    TRANSCRIBER = "Transcriber"
    VOICE = "Voice"


class TrendTypes(ChoiceEnum):
    positive = "Positive"
    negative = "Negative"


class ProductTypes(ChoiceEnum):
    telephony_sip = "telephony_sip"
    voice_infra = "voice_infra"
    ai_agents = "ai_agents"
    communication_space = "communication_space"


class Regions(ChoiceEnum):
    IN = "India"
    US = "United States"
    EU = "Europe"
    AUS = "Australia"
    UAE = "United Arab Emirates"


class InvoiceStatus(ChoiceEnum):
    pending = "Pending"
    paid = "Paid"
    failed = "Failed"
    cancelled = "Cancelled"
    refunded = "Refunded"


class MetricTypes(ChoiceEnum):
    Telephony = "telephony"
    Agents = "agents"


class Product(ChoiceEnum):
    Ai = "unpod.ai"
    Dev = "unpod.dev"


class RequiredInfoOptions(ChoiceEnum):
    location = "Location"
    file_workbook = "File Workbook"
    file_doc = "File Document"
    file_image = "File Image"
    login = "Login"
    subscription = "Subscription"


class StatusEnum(ChoiceEnum):
    pending = "Pending"
    processing = "Processing"
    completed = "Completed"
    failed = "Failed"
