import datetime as dt

from .types import CoverLetterData

DUMMY_COVER_LETTER_DATA = CoverLetterData(
    name="Jane Smith",
    title="Senior Software Engineer",
    email="jane.smith@example.com",
    phone="(555) 123-4567",
    date=dt.date.today(),
    body_paragraphs=[
        "I am writing to express my strong interest in the Senior Software Engineer position at your company. With over 8 years of experience in software development and a proven track record of delivering high-quality solutions, I am confident that I would be a valuable addition to your team.",
        "Throughout my career, I have developed expertise in full-stack development, cloud architecture, and agile methodologies. My experience includes leading cross-functional teams, designing scalable systems, and implementing best practices that have consistently improved product quality and team efficiency. I am particularly drawn to your company's commitment to innovation and technical excellence.",
        "I would welcome the opportunity to discuss how my skills and experience align with your team's needs. Thank you for considering my application. I look forward to hearing from you soon.",
    ],
)
