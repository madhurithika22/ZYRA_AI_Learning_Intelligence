import asyncio
import os
import sys
from pathlib import Path

# Add apps/api to Python path so app modules can be imported directly
api_path = Path(__file__).resolve().parent.parent / "apps" / "api"
if str(api_path) not in sys.path:
    sys.path.insert(0, str(api_path))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.assessment import Assessment
from app.models.assessment_question import AssessmentQuestion
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.models.learning_resource import LearningResource
from app.models.role import Role
from app.models.role_skill import RoleSkill
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.models.skill_relation import SkillRelation
from app.models.skill_resource import SkillResource


async def seed_roles(session: AsyncSession) -> dict[str, Role]:
    roles_data = [
        {
            "name": "AI Engineer",
            "description": "Engineers scalable AI systems, fine-tunes deep learning models, and manages MLOps infrastructure.",
        },
        {
            "name": "ML Engineer",
            "description": "Designs machine learning pipelines, feature stores, and predictive backend services.",
        },
        {
            "name": "Data Scientist",
            "description": "Analyzes complex datasets, builds statistical models, and extracts actionable business insights.",
        },
    ]

    roles_map: dict[str, Role] = {}
    for data in roles_data:
        stmt = select(Role).where(Role.name == data["name"])
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            role = Role(**data)
            session.add(role)
            await session.flush()
        else:
            role.description = data["description"]
        roles_map[role.name] = role

    return roles_map


async def seed_skills(session: AsyncSession) -> dict[str, Skill]:
    skills_data = [
        {"name": "Python", "description": "Core Python language features, data structures, and async programming.", "difficulty": 1.0, "parent": None},
        {"name": "Statistics", "description": "Probability theory, hypothesis testing, distributions, and inferential statistics.", "difficulty": 2.0, "parent": None},
        {"name": "Linear Algebra", "description": "Vector spaces, matrices, eigenvalues, and linear transformations.", "difficulty": 2.0, "parent": None},
        {"name": "Machine Learning", "description": "Supervised, unsupervised algorithms, cross-validation, and model evaluation.", "difficulty": 2.5, "parent": None},
        {"name": "Deep Learning", "description": "Neural network architectures, backpropagation, CNNs, and Transformers.", "difficulty": 3.5, "parent": "Machine Learning"},
        {"name": "PyTorch", "description": "Deep learning tensor operations, autograd, and PyTorch model training.", "difficulty": 3.0, "parent": "Deep Learning"},
        {"name": "Docker", "description": "Containerization, Dockerfile creation, multi-stage builds, and networking.", "difficulty": 2.0, "parent": None},
        {"name": "Model Deployment", "description": "Serving models via REST/gRPC APIs, quantization, and batch inference.", "difficulty": 3.0, "parent": "Docker"},
        {"name": "MLOps", "description": "Continuous training pipelines, model monitoring, registry, and orchestration.", "difficulty": 4.0, "parent": "Model Deployment"},
        {"name": "System Design", "description": "High-availability system architecture, caching, queues, and database design.", "difficulty": 3.5, "parent": None},
    ]

    skills_map: dict[str, Skill] = {}

    for data in skills_data:
        stmt = select(Skill).where(Skill.name == data["name"])
        result = await session.execute(stmt)
        skill = result.scalar_one_or_none()
        if not skill:
            skill = Skill(
                name=data["name"],
                description=data["description"],
                difficulty=data["difficulty"],
            )
            session.add(skill)
            await session.flush()
        else:
            skill.description = data["description"]
            skill.difficulty = data["difficulty"]
        skills_map[skill.name] = skill

    for data in skills_data:
        if data["parent"]:
            parent_skill = skills_map[data["parent"]]
            child_skill = skills_map[data["name"]]
            child_skill.parent_skill_id = parent_skill.id

    await session.flush()
    return skills_map


async def seed_prerequisites(session: AsyncSession, skills: dict[str, Skill]) -> None:
    prereqs = [
        ("Statistics", "Machine Learning", "prerequisite", 1.0),
        ("Linear Algebra", "Machine Learning", "prerequisite", 1.0),
        ("Machine Learning", "Deep Learning", "prerequisite", 1.0),
        ("Deep Learning", "PyTorch", "prerequisite", 0.9),
        ("Docker", "Model Deployment", "prerequisite", 1.0),
        ("Model Deployment", "MLOps", "prerequisite", 1.0),
        ("Python", "Machine Learning", "supports", 0.8),
        ("System Design", "MLOps", "supports", 0.9),
    ]

    for source_name, target_name, rel_type, strength in prereqs:
        source = skills[source_name]
        target = skills[target_name]

        stmt = select(SkillRelation).where(
            SkillRelation.source_skill_id == source.id,
            SkillRelation.target_skill_id == target.id,
            SkillRelation.relation_type == rel_type,
        )
        result = await session.execute(stmt)
        relation = result.scalar_one_or_none()
        if not relation:
            relation = SkillRelation(
                source_skill_id=source.id,
                target_skill_id=target.id,
                relation_type=rel_type,
                strength=strength,
            )
            session.add(relation)
    await session.flush()


async def seed_role_skills(
    session: AsyncSession, roles: dict[str, Role], skills: dict[str, Skill]
) -> None:
    role_skill_mappings = [
        ("AI Engineer", "Python", 1.0, 4.0),
        ("AI Engineer", "Machine Learning", 1.0, 4.0),
        ("AI Engineer", "Deep Learning", 1.0, 4.5),
        ("AI Engineer", "PyTorch", 0.9, 4.0),
        ("AI Engineer", "Model Deployment", 0.9, 3.5),
        ("AI Engineer", "MLOps", 0.8, 3.5),
        ("AI Engineer", "System Design", 0.8, 3.0),
        ("ML Engineer", "Python", 1.0, 4.0),
        ("ML Engineer", "Statistics", 0.9, 3.5),
        ("ML Engineer", "Linear Algebra", 0.8, 3.0),
        ("ML Engineer", "Machine Learning", 1.0, 4.0),
        ("ML Engineer", "Docker", 0.9, 3.5),
        ("ML Engineer", "Model Deployment", 1.0, 4.0),
        ("Data Scientist", "Python", 1.0, 4.0),
        ("Data Scientist", "Statistics", 1.0, 4.5),
        ("Data Scientist", "Linear Algebra", 0.9, 4.0),
        ("Data Scientist", "Machine Learning", 0.9, 3.5),
    ]

    for role_name, skill_name, importance, req_level in role_skill_mappings:
        role = roles[role_name]
        skill = skills[skill_name]

        stmt = select(RoleSkill).where(
            RoleSkill.role_id == role.id,
            RoleSkill.skill_id == skill.id,
        )
        result = await session.execute(stmt)
        rs = result.scalar_one_or_none()
        if not rs:
            rs = RoleSkill(
                role_id=role.id,
                skill_id=skill.id,
                importance=importance,
                required_level=req_level,
            )
            session.add(rs)
        else:
            rs.importance = importance
            rs.required_level = req_level
    await session.flush()


async def seed_resources(
    session: AsyncSession, skills: dict[str, Skill]
) -> dict[str, LearningResource]:
    resources_data = [
        {
            "title": "Python for Data Science & ML Fundamentals",
            "description": "Comprehensive practical guide to Python, NumPy, and Pandas for ML workflows.",
            "resource_type": "course",
            "difficulty": 1.5,
            "estimated_minutes": 240,
            "source_url": "/resources/python-fundamentals",
            "skill_name": "Python",
        },
        {
            "title": "Statistical Inference & Probability for Engineers",
            "description": "Foundational course on probability distributions, hypothesis testing, and Bayesian analysis.",
            "resource_type": "course",
            "difficulty": 2.5,
            "estimated_minutes": 360,
            "source_url": "/resources/statistical-inference",
            "skill_name": "Statistics",
        },
        {
            "title": "Applied Machine Learning Algorithms Deep Dive",
            "description": "Hands-on project implementing decision trees, SVMs, and ensemble methods from scratch.",
            "resource_type": "project",
            "difficulty": 2.8,
            "estimated_minutes": 480,
            "source_url": "/resources/applied-ml",
            "skill_name": "Machine Learning",
        },
        {
            "title": "Deep Neural Networks Architecture & Optimization",
            "description": "Comprehensive exploration of backpropagation, vanishing gradients, and modern optimizer variants.",
            "resource_type": "video",
            "difficulty": 3.5,
            "estimated_minutes": 300,
            "source_url": "/resources/deep-neural-nets",
            "skill_name": "Deep Learning",
        },
        {
            "title": "PyTorch Production Model Building & Fine-tuning",
            "description": "Build, fine-tune, and optimize custom PyTorch modules and training loops.",
            "resource_type": "exercise",
            "difficulty": 3.2,
            "estimated_minutes": 180,
            "source_url": "/resources/pytorch-production",
            "skill_name": "PyTorch",
        },
        {
            "title": "Docker Containerization for Machine Learning Engineers",
            "description": "Build optimized Docker containers for GPU workloads and microservice deployment.",
            "resource_type": "course",
            "difficulty": 2.2,
            "estimated_minutes": 150,
            "source_url": "/resources/docker-ml",
            "skill_name": "Docker",
        },
        {
            "title": "Production Model Serving with FastAPI & Triton",
            "description": "Deploy high-throughput inference endpoints with model batching and async workers.",
            "resource_type": "project",
            "difficulty": 3.5,
            "estimated_minutes": 300,
            "source_url": "/resources/model-serving",
            "skill_name": "Model Deployment",
        },
        {
            "title": "End-to-End MLOps Pipelines & Continuous Training",
            "description": "Set up automated ML pipelines with experiment tracking, drift detection, and CI/CD.",
            "resource_type": "course",
            "difficulty": 4.0,
            "estimated_minutes": 420,
            "source_url": "/resources/mlops-pipelines",
            "skill_name": "MLOps",
        },
    ]

    resources_map: dict[str, LearningResource] = {}
    for data in resources_data:
        skill_name = data.pop("skill_name")
        stmt = select(LearningResource).where(
            LearningResource.title == data["title"]
        )
        result = await session.execute(stmt)
        resource = result.scalar_one_or_none()
        if not resource:
            resource = LearningResource(**data)
            session.add(resource)
            await session.flush()

        resources_map[resource.title] = resource

        skill = skills[skill_name]
        sr_stmt = select(SkillResource).where(
            SkillResource.skill_id == skill.id,
            SkillResource.resource_id == resource.id,
        )
        sr_result = await session.execute(sr_stmt)
        sr = sr_result.scalar_one_or_none()
        if not sr:
            sr = SkillResource(skill_id=skill.id, resource_id=resource.id, relevance=1.0)
            session.add(sr)

    await session.flush()
    return resources_map


async def seed_assessments(
    session: AsyncSession, skills: dict[str, Skill]
) -> None:
    assessments_data = [
        {
            "title": "Adaptive Diagnostic Item Bank",
            "assessment_type": "diagnostic",
            "skill_name": "Machine Learning",
            "description": "Multi-difficulty, multi-type question bank for adaptive diagnostic evaluation.",
            "questions": [
                # Python Questions
                {
                    "skill_name": "Python",
                    "prompt": "What is the time complexity of looking up a key in a Python dictionary on average?",
                    "question_type": "multiple_choice",
                    "difficulty": 1.0,
                    "expected_answer": {"correct_option": "O(1)", "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"]},
                },
                {
                    "skill_name": "Python",
                    "prompt": "Write a Python list comprehension that filters even numbers from `[1, 2, 3, 4, 5, 6]`.",
                    "question_type": "coding",
                    "difficulty": 2.0,
                    "expected_answer": {"required_keywords": ["[x for x in", "if x % 2 == 0]"], "correct_answer": "[x for x in numbers if x % 2 == 0]"},
                },
                # Statistics Questions
                {
                    "skill_name": "Statistics",
                    "prompt": "What does a p-value less than 0.05 signify in a hypothesis test?",
                    "question_type": "short_answer",
                    "difficulty": 2.0,
                    "expected_answer": {"required_keywords": ["reject", "null hypothesis", "statistically significant"]},
                },
                {
                    "skill_name": "Statistics",
                    "prompt": "In a skewed distribution with a long right tail, how do mean and median compare?",
                    "question_type": "multiple_choice",
                    "difficulty": 3.0,
                    "expected_answer": {"correct_option": "Mean > Median", "options": ["Mean < Median", "Mean = Median", "Mean > Median", "Cannot be determined"]},
                },
                # Machine Learning Questions
                {
                    "skill_name": "Machine Learning",
                    "prompt": "Which technique helps prevent overfitting by penalizing the magnitude of model weights?",
                    "question_type": "multiple_choice",
                    "difficulty": 2.0,
                    "expected_answer": {"correct_option": "Regularization", "options": ["Gradient Descent", "Regularization", "Data Augmentation", "One-Hot Encoding"]},
                },
                {
                    "skill_name": "Machine Learning",
                    "prompt": "Explain the trade-off between Bias and Variance in supervised learning models.",
                    "question_type": "scenario",
                    "difficulty": 3.0,
                    "expected_answer": {"required_keywords": ["underfitting", "overfitting", "flexibility", "generalization"]},
                },
                # Deep Learning Questions
                {
                    "skill_name": "Deep Learning",
                    "prompt": "Which activation function helps mitigate the vanishing gradient problem in deep networks?",
                    "question_type": "multiple_choice",
                    "difficulty": 3.0,
                    "expected_answer": {"correct_option": "ReLU", "options": ["Sigmoid", "Tanh", "ReLU", "Step"]},
                },
                {
                    "skill_name": "Deep Learning",
                    "prompt": "Describe how Self-Attention mechanisms compute alignment scores in Transformer models.",
                    "question_type": "scenario",
                    "difficulty": 4.5,
                    "expected_answer": {"required_keywords": ["query", "key", "value", "softmax", "scaled dot product"]},
                },
                # PyTorch Questions
                {
                    "skill_name": "PyTorch",
                    "prompt": "What command in PyTorch resets accumulated gradients before running `loss.backward()`?",
                    "question_type": "short_answer",
                    "difficulty": 2.0,
                    "expected_answer": {"correct_answer": "optimizer.zero_grad()", "required_keywords": ["zero_grad"]},
                },
                # Model Deployment Questions
                {
                    "skill_name": "Model Deployment",
                    "prompt": "Which component manages high-throughput async inference requests in Triton Inference Server?",
                    "question_type": "multiple_choice",
                    "difficulty": 3.5,
                    "expected_answer": {"correct_option": "Dynamic Batcher", "options": ["Dynamic Batcher", "Static Router", "Load Balancer", "DNS Resolver"]},
                },
                {
                    "skill_name": "Model Deployment",
                    "prompt": "How does FastAPI serve concurrent inference requests asynchronously?",
                    "question_type": "short_answer",
                    "difficulty": 3.0,
                    "expected_answer": {"correct_answer": "async def with ASGI event loop", "required_keywords": ["async", "event loop", "asgi"]},
                },
                # MLOps Questions
                {
                    "skill_name": "MLOps",
                    "prompt": "What is concept drift in production machine learning systems?",
                    "question_type": "short_answer",
                    "difficulty": 3.5,
                    "expected_answer": {"required_keywords": ["statistical properties", "target variable", "relationship", "input features"]},
                },
                {
                    "skill_name": "MLOps",
                    "prompt": "Design an automated CI/CD and deployment strategy for a real-time LLM inference microservice.",
                    "question_type": "scenario",
                    "difficulty": 5.0,
                    "expected_answer": {"required_keywords": ["canary deployment", "health check", "latency SLA", "rollback", "shadow testing"]},
                },
            ],
        },
    ]

    for data in assessments_data:
        skill_name = data.pop("skill_name")
        questions_data = data.pop("questions")

        skill = skills[skill_name]
        stmt = select(Assessment).where(Assessment.title == data["title"])
        result = await session.execute(stmt)
        assessment = result.scalar_one_or_none()
        if not assessment:
            assessment = Assessment(
                title=data["title"],
                assessment_type=data["assessment_type"],
                skill_id=skill.id,
                description=data["description"],
            )
            session.add(assessment)
            await session.flush()

        for q_data in questions_data:
            q_skill = skills[q_data.pop("skill_name")]
            q_stmt = select(AssessmentQuestion).where(
                AssessmentQuestion.assessment_id == assessment.id,
                AssessmentQuestion.prompt == q_data["prompt"],
            )
            q_result = await session.execute(q_stmt)
            question = q_result.scalar_one_or_none()
            if not question:
                question = AssessmentQuestion(
                    assessment_id=assessment.id,
                    skill_id=q_skill.id,
                    **q_data,
                )
                session.add(question)

    await session.flush()


async def seed_demo_learner_profile(
    session: AsyncSession,
    roles: dict[str, Role],
    skills: dict[str, Skill],
    resources: dict[str, LearningResource],
) -> None:
    # 1. Learner
    email = "alex.chen@example.com"
    stmt = select(Learner).where(Learner.email == email)
    result = await session.execute(stmt)
    learner = result.scalar_one_or_none()
    if not learner:
        learner = Learner(
            display_name="Alex Chen",
            email=email,
        )
        session.add(learner)
        await session.flush()

    # 2. Goal
    ai_role = roles["AI Engineer"]
    goal_stmt = select(Goal).where(
        Goal.learner_id == learner.id,
        Goal.target_role_id == ai_role.id,
    )
    goal_result = await session.execute(goal_stmt)
    goal = goal_result.scalar_one_or_none()
    if not goal:
        goal = Goal(
            learner_id=learner.id,
            target_role_id=ai_role.id,
            objective="Transition to Senior AI Engineer with mastery in PyTorch and MLOps",
            timeline_weeks=12,
            daily_minutes=60,
        )
        session.add(goal)
        await session.flush()

    # Note: Initial mastery records for demo learner are seeded conservatively
    mastery_data = [
        ("Python", 0.84, 0.95),
        ("Statistics", 0.60, 0.85),
        ("Linear Algebra", 0.64, 0.88),
        ("Machine Learning", 0.70, 0.90),
        ("Deep Learning", 0.40, 0.70),
        ("PyTorch", 0.30, 0.60),
        ("Docker", 0.60, 0.80),
        ("Model Deployment", 0.24, 0.50),
        ("MLOps", 0.20, 0.40),
    ]


    for skill_name, score, conf in mastery_data:
        sk = skills[skill_name]
        sm_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == learner.id,
            SkillMastery.skill_id == sk.id,
        )
        sm_result = await session.execute(sm_stmt)
        sm = sm_result.scalar_one_or_none()
        if not sm:
            sm = SkillMastery(
                learner_id=learner.id,
                skill_id=sk.id,
                mastery_score=score,
                confidence=conf,
            )
            session.add(sm)
        else:
            sm.mastery_score = score
            sm.confidence = conf


    await session.flush()

    # Learning Path & Nodes
    path_stmt = select(LearningPath).where(
        LearningPath.learner_id == learner.id,
        LearningPath.goal_id == goal.id,
    )
    path_result = await session.execute(path_stmt)
    learning_path = path_result.scalar_one_or_none()
    if not learning_path:
        learning_path = LearningPath(
            learner_id=learner.id,
            goal_id=goal.id,
            name="Alex's AI Engineer Mastery Path",
            strategy="balanced",
            status="active",
            estimated_minutes=1200,
            expected_readiness=0.85,
        )
        session.add(learning_path)
        await session.flush()

    node_steps = [
        (1, "Deep Neural Networks Architecture & Optimization", "Deep Learning", "Deep Learning Foundations", 300, "Strengthen deep neural network principles."),
        (2, "PyTorch Production Model Building & Fine-tuning", "PyTorch", "PyTorch Specialization", 180, "Hands-on PyTorch model training."),
        (3, "Production Model Serving with FastAPI & Triton", "Model Deployment", "Model Serving Deployment", 300, "Learn production model serving."),
        (4, "End-to-End MLOps Pipelines & Continuous Training", "MLOps", "MLOps Pipeline Integration", 420, "Master complete MLOps lifecycle."),
    ]

    for seq, res_title, skill_name, label, minutes, rationale in node_steps:
        res = resources[res_title]
        sk = skills[skill_name]

        node_stmt = select(LearningPathNode).where(
            LearningPathNode.learning_path_id == learning_path.id,
            LearningPathNode.sequence == seq,
        )
        node_result = await session.execute(node_stmt)
        node = node_result.scalar_one_or_none()
        if not node:
            node = LearningPathNode(
                learning_path_id=learning_path.id,
                sequence=seq,
                resource_id=res.id,
                skill_id=sk.id,
                milestone_label=label,
                estimated_minutes=minutes,
                rationale=rationale,
            )
            session.add(node)

    await session.flush()


async def seed_all() -> None:
    print("Starting idempotent database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            roles = await seed_roles(session)
            skills = await seed_skills(session)
            await seed_prerequisites(session, skills)
            await seed_role_skills(session, roles, skills)
            resources = await seed_resources(session, skills)
            await seed_assessments(session, skills)
            await seed_demo_learner_profile(session, roles, skills, resources)

    print("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_all())
