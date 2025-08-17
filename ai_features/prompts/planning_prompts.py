"""
Planning Prompts

Templates for task planning and workflow generation.
"""

from typing import Dict, Any, List


class PlanningPrompts:
    """Collection of planning prompt templates"""
    
    @staticmethod
    def generate_todo_list(user_request: str, site_analysis: Dict[str, Any]) -> str:
        """Prompt for generating comprehensive todo lists"""
        return f"""
        You are an expert web development project manager. Generate a detailed todo list for this website modification request.
        
        User Request: "{user_request}"
        
        Site Analysis:
        {site_analysis}
        
        Create a comprehensive, ordered list of specific, actionable tasks. Each task should be:
        1. Specific and measurable
        2. Technically feasible
        3. Properly sequenced with dependencies
        4. Scoped to individual files or components
        
        Return as JSON array:
        [
            {{
                "id": "task_1",
                "title": "Brief task title",
                "description": "Detailed description of what needs to be done",
                "task_type": "analyze|design|implement|test|deploy|optimize",
                "category": "content|styling|functionality|structure|performance",
                "priority": "critical|high|medium|low",
                "estimated_hours": 1.0,
                "complexity": "low|medium|high",
                "files_affected": ["file1.html", "style.css"],
                "dependencies": ["task_id1", "task_id2"],
                "skills_required": ["html", "css", "javascript"],
                "success_criteria": "Specific criteria for completion",
                "potential_risks": ["risk1", "risk2"],
                "llm_instructions": "Specific instructions for AI execution"
            }}
        ]
        
        Ensure tasks are granular enough to be completed in 1-4 hours each.
        Include both implementation and validation tasks.
        """
    
    @staticmethod
    def task_prioritization(tasks: List[Dict[str, Any]], constraints: Dict[str, Any]) -> str:
        """Prompt for task prioritization and scheduling"""
        return f"""
        Prioritize and schedule these website modification tasks.
        
        Tasks: {tasks}
        Constraints: {constraints}
        
        Consider:
        1. Technical dependencies
        2. Business impact
        3. User experience priorities
        4. Risk factors
        5. Resource requirements
        
        Return prioritized task order with reasoning:
        {{
            "execution_order": [
                {{
                    "task_id": "task_1",
                    "order": 1,
                    "reasoning": "Why this task should be done first",
                    "parallel_group": "A",
                    "estimated_start": "Phase 1",
                    "blocking_tasks": ["task_2", "task_3"]
                }}
            ],
            "phases": {{
                "phase_1": {{
                    "name": "Foundation",
                    "tasks": ["task_1", "task_2"],
                    "goals": ["goal1", "goal2"]
                }}
            }},
            "critical_path": ["task_1", "task_3", "task_5"],
            "parallel_opportunities": [["task_2", "task_4"]],
            "risk_mitigation": {{
                "high_risk_tasks": ["task_id"],
                "mitigation_strategies": ["strategy1", "strategy2"]
            }}
        }}
        """
    
    @staticmethod
    def implementation_strategy(task: Dict[str, Any], site_context: Dict[str, Any]) -> str:
        """Prompt for detailed implementation strategy"""
        return f"""
        Create a detailed implementation strategy for this specific task.
        
        Task: {task}
        Site Context: {site_context}
        
        Develop a step-by-step implementation plan:
        
        Return JSON:
        {{
            "approach": "incremental|complete_rewrite|patch|enhancement",
            "implementation_steps": [
                {{
                    "step": 1,
                    "action": "Specific action to take",
                    "files_to_modify": ["file1.html"],
                    "code_changes": "Description of changes",
                    "validation_method": "How to verify this step",
                    "rollback_plan": "How to undo if needed"
                }}
            ],
            "technical_considerations": {{
                "browser_compatibility": ["modern", "IE11", "mobile"],
                "performance_impact": "minimal|moderate|significant",
                "accessibility_requirements": ["requirement1", "requirement2"],
                "seo_considerations": ["consideration1", "consideration2"]
            }},
            "testing_strategy": {{
                "manual_tests": ["test1", "test2"],
                "automated_checks": ["validation1", "validation2"],
                "user_acceptance_criteria": ["criteria1", "criteria2"]
            }},
            "deployment_plan": {{
                "backup_requirements": ["file1", "file2"],
                "deployment_order": ["step1", "step2"],
                "verification_checklist": ["check1", "check2"]
            }},
            "contingency_plans": {{
                "common_issues": ["issue1", "issue2"],
                "solutions": ["solution1", "solution2"]
            }}
        }}
        """
    
    @staticmethod
    def resource_estimation(tasks: List[Dict[str, Any]]) -> str:
        """Prompt for estimating resources and timeline"""
        return f"""
        Estimate the resources and timeline for these website modification tasks.
        
        Tasks: {tasks}
        
        Provide realistic estimates considering:
        1. Task complexity and dependencies
        2. Potential technical challenges
        3. Quality assurance requirements
        4. Buffer time for iterations
        
        Return JSON:
        {{
            "overall_timeline": {{
                "estimated_total_hours": 0,
                "estimated_days": 0,
                "confidence_level": "low|medium|high",
                "critical_path_duration": 0
            }},
            "resource_breakdown": {{
                "analysis_hours": 0,
                "design_hours": 0,
                "development_hours": 0,
                "testing_hours": 0,
                "deployment_hours": 0
            }},
            "skill_requirements": {{
                "html_css": "basic|intermediate|advanced",
                "javascript": "basic|intermediate|advanced",
                "design": "basic|intermediate|advanced",
                "seo": "basic|intermediate|advanced"
            }},
            "risk_factors": {{
                "technical_risks": ["risk1", "risk2"],
                "timeline_risks": ["risk1", "risk2"],
                "mitigation_strategies": ["strategy1", "strategy2"]
            }},
            "milestones": [
                {{
                    "name": "Milestone 1",
                    "deliverables": ["deliverable1", "deliverable2"],
                    "estimated_completion": "day 3"
                }}
            ]
        }}
        """
    
    @staticmethod
    def change_management_plan(changes: List[Dict[str, Any]], site_context: Dict[str, Any]) -> str:
        """Prompt for creating change management strategy"""
        return f"""
        Create a change management plan for these website modifications.
        
        Proposed Changes: {changes}
        Site Context: {site_context}
        
        Develop a comprehensive change management strategy:
        
        Return JSON:
        {{
            "change_analysis": {{
                "scope": "minor|moderate|major|critical",
                "user_impact": "none|minimal|moderate|significant",
                "business_impact": "none|minimal|moderate|significant",
                "technical_complexity": "low|medium|high|critical"
            }},
            "stakeholder_communication": {{
                "notification_required": true/false,
                "approval_needed": true/false,
                "user_training_required": true/false,
                "documentation_updates": ["doc1", "doc2"]
            }},
            "rollout_strategy": {{
                "approach": "immediate|phased|gradual|pilot",
                "phases": [
                    {{
                        "name": "Phase 1",
                        "scope": "Limited rollout",
                        "success_criteria": ["criteria1", "criteria2"]
                    }}
                ],
                "rollback_triggers": ["trigger1", "trigger2"]
            }},
            "quality_assurance": {{
                "pre_deployment_checks": ["check1", "check2"],
                "post_deployment_monitoring": ["metric1", "metric2"],
                "success_metrics": ["metric1", "metric2"]
            }},
            "risk_management": {{
                "identified_risks": [
                    {{
                        "risk": "Description",
                        "probability": "low|medium|high",
                        "impact": "low|medium|high",
                        "mitigation": "Mitigation strategy"
                    }}
                ],
                "contingency_plans": ["plan1", "plan2"]
            }}
        }}
        """
    
    @staticmethod
    def optimization_roadmap(current_state: Dict[str, Any], goals: List[str]) -> str:
        """Prompt for creating optimization roadmap"""
        return f"""
        Create an optimization roadmap for this website.
        
        Current State: {current_state}
        Goals: {goals}
        
        Develop a strategic roadmap for improvements:
        
        Return JSON:
        {{
            "optimization_phases": [
                {{
                    "phase": "Phase 1: Foundation",
                    "duration": "2-4 weeks", 
                    "objectives": ["objective1", "objective2"],
                    "key_activities": ["activity1", "activity2"],
                    "success_metrics": ["metric1", "metric2"],
                    "deliverables": ["deliverable1", "deliverable2"]
                }}
            ],
            "quick_wins": [
                {{
                    "improvement": "Description",
                    "effort": "low|medium|high",
                    "impact": "low|medium|high",
                    "timeline": "1-3 days"
                }}
            ],
            "long_term_initiatives": [
                {{
                    "initiative": "Description",
                    "strategic_value": "Description",
                    "effort_required": "months",
                    "dependencies": ["dependency1", "dependency2"]
                }}
            ],
            "performance_targets": {{
                "page_load_time": "target value",
                "mobile_score": "target value",
                "seo_score": "target value",
                "accessibility_score": "target value"
            }},
            "technology_evolution": {{
                "current_stack": "assessment",
                "recommended_upgrades": ["upgrade1", "upgrade2"],
                "migration_strategy": "approach description"
            }}
        }}
        """
    
    @staticmethod
    def feature_specification(feature_request: str, technical_constraints: Dict[str, Any]) -> str:
        """Prompt for detailed feature specification"""
        return f"""
        Create a detailed specification for this feature request.
        
        Feature Request: "{feature_request}"
        Technical Constraints: {technical_constraints}
        
        Develop comprehensive feature specifications:
        
        Return JSON:
        {{
            "feature_overview": {{
                "name": "Feature name",
                "description": "Detailed description",
                "user_problem": "Problem this solves",
                "business_value": "Why this feature matters"
            }},
            "functional_requirements": [
                {{
                    "requirement": "REQ-001",
                    "description": "Specific requirement",
                    "priority": "must_have|should_have|could_have|wont_have",
                    "acceptance_criteria": ["criteria1", "criteria2"]
                }}
            ],
            "technical_requirements": {{
                "technologies": ["html", "css", "javascript"],
                "integrations": ["service1", "service2"],
                "performance_requirements": ["requirement1", "requirement2"],
                "security_considerations": ["consideration1", "consideration2"]
            }},
            "user_experience": {{
                "user_flows": ["flow1", "flow2"],
                "interface_elements": ["element1", "element2"],
                "accessibility_requirements": ["requirement1", "requirement2"],
                "mobile_considerations": ["consideration1", "consideration2"]
            }},
            "implementation_approach": {{
                "development_phases": ["phase1", "phase2"],
                "technical_approach": "Description",
                "integration_points": ["point1", "point2"],
                "data_requirements": ["requirement1", "requirement2"]
            }},
            "testing_strategy": {{
                "test_scenarios": ["scenario1", "scenario2"],
                "edge_cases": ["case1", "case2"],
                "performance_tests": ["test1", "test2"],
                "user_testing_plan": "Description"
            }}
        }}
        """