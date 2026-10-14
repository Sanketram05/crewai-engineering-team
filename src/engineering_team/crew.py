from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai import LLM
import os
from dotenv import load_dotenv
load_dotenv()

llm = LLM(
    model="gpt-4.1",
    base_url="https://api.mixroute.ai/v1",
    api_key=os.getenv("MIXROUTE_API_KEY")
)

llm1 = LLM(
    model="deepseek-v4-flash",
    base_url="https://api.mixroute.ai/v1",
    api_key=os.getenv("MIXROUTE_API_KEY")
)

@CrewBase
class EngineeringTeam():
    """EngineeringTeam crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],
            llm=llm,
            verbose=True
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            llm=llm,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=240,
            max_retries=5,
            verbose=True
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],
            llm=llm,
            verbose=True
        )
    
    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],
            llm=llm,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=240,
            max_retries=5,
            verbose=True
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'], 
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],
        )
    
    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],
        )
    
    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeam crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
        )
