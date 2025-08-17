"""
Analysis Prompts

Templates for website analysis and understanding tasks.
"""

from typing import Dict, Any, List


class AnalysisPrompts:
    """Collection of analysis prompt templates"""
    
    @staticmethod
    def website_structure_analysis(pages: List[str], components: Dict[str, Any]) -> str:
        """Prompt for analyzing website structure"""
        return f"""
        You are an AI website analyzer. Analyze the structure of this converted WordPress site.
        
        Pages found: {len(pages)}
        {chr(10).join(f"- {page}" for page in pages[:10])}
        {"..." if len(pages) > 10 else ""}
        
        Components detected: {list(components.keys())}
        
        Provide analysis in JSON format:
        {{
            "site_type": "business|portfolio|blog|ecommerce|other",
            "navigation_pattern": "horizontal|vertical|dropdown|mega",
            "content_structure": "hierarchical|flat|mixed",
            "design_style": "modern|traditional|minimal|complex",
            "target_audience": "general|business|technical|creative",
            "key_features": ["list", "of", "features"],
            "potential_improvements": ["improvement1", "improvement2"]
        }}
        
        Focus on understanding the site's purpose and structure.
        """
    
    @staticmethod
    def content_pattern_analysis(page_content: Dict[str, Any]) -> str:
        """Prompt for analyzing content patterns"""
        return f"""
        Analyze the content patterns across this website's pages.
        
        Page Data:
        {page_content}
        
        Identify:
        1. Common content types (text, images, forms, etc.)
        2. Heading hierarchy patterns
        3. Content organization methods
        4. Recurring content blocks
        5. User interaction elements
        
        Return analysis as JSON:
        {{
            "content_types": {{"type": "frequency"}},
            "heading_patterns": ["pattern1", "pattern2"],
            "organization_style": "grid|list|cards|mixed",
            "interactive_elements": ["forms", "buttons", "links"],
            "content_density": "sparse|moderate|dense"
        }}
        """
    
    @staticmethod
    def technology_stack_analysis(file_structure: Dict[str, Any], scripts: List[str], styles: List[str]) -> str:
        """Prompt for analyzing technology stack"""
        return f"""
        Analyze the technology stack of this website.
        
        File Structure: {file_structure}
        JavaScript files: {scripts}
        CSS files: {styles}
        
        Identify:
        1. Frontend framework (if any)
        2. CSS framework/library
        3. JavaScript libraries
        4. Build tools or preprocessors
        5. Responsive design approach
        
        Return as JSON:
        {{
            "frontend_framework": "none|react|vue|angular|other",
            "css_framework": "bootstrap|tailwind|foundation|custom|other", 
            "js_libraries": ["jquery", "bootstrap", "etc"],
            "build_tools": ["webpack", "gulp", "etc"],
            "responsive_approach": "mobile-first|desktop-first|adaptive|none",
            "modern_features": ["css-grid", "flexbox", "css-variables", "etc"]
        }}
        """
    
    @staticmethod
    def user_request_analysis(request: str, site_context: Dict[str, Any]) -> str:
        """Prompt for analyzing user editing requests"""
        return f"""
        Analyze this user request for website modifications.
        
        User Request: "{request}"
        
        Site Context:
        {site_context}
        
        Analyze and categorize the request:
        
        Return JSON:
        {{
            "intent": "add_feature|modify_content|style_change|structure_change|fix_issue|optimize",
            "scope": "single_page|multiple_pages|site_wide|global_component",
            "complexity": "low|medium|high",
            "technical_requirements": ["html", "css", "javascript", "etc"],
            "affected_areas": ["header", "navigation", "content", "footer", "styling"],
            "user_goals": ["goal1", "goal2"],
            "potential_challenges": ["challenge1", "challenge2"],
            "success_criteria": ["criteria1", "criteria2"]
        }}
        
        Focus on understanding what the user truly wants to achieve.
        """
    
    @staticmethod
    def change_impact_analysis(file_path: str, target_content: str, site_memory: Dict[str, Any]) -> str:
        """Prompt for analyzing impact of proposed changes"""
        return f"""
        Analyze the potential impact of modifying this content.
        
        File: {file_path}
        Target Content: "{target_content}"
        
        Site Memory:
        {site_memory}
        
        Assess the impact:
        
        Return JSON:
        {{
            "impact_level": "low|medium|high|critical",
            "affected_components": ["nav", "layout", "styling", "etc"],
            "breaking_changes": ["potential", "issues"],
            "dependencies": ["file1.css", "file2.js"],
            "user_visible_changes": ["change1", "change2"],
            "seo_impact": "none|positive|negative",
            "performance_impact": "none|positive|negative",
            "accessibility_impact": "none|positive|negative",
            "recommendations": ["rec1", "rec2"]
        }}
        
        Consider all aspects: functionality, design, user experience, and technical implications.
        """
    
    @staticmethod
    def content_quality_analysis(content: str, context: str) -> str:
        """Prompt for analyzing content quality"""
        return f"""
        Analyze the quality and characteristics of this website content.
        
        Content: "{content[:1000]}{'...' if len(content) > 1000 else ''}"
        Context: {context}
        
        Evaluate:
        1. Content clarity and readability
        2. SEO optimization
        3. User engagement potential
        4. Accessibility considerations
        5. Brand consistency
        
        Return JSON:
        {{
            "readability_score": "poor|fair|good|excellent",
            "seo_optimization": "poor|fair|good|excellent",
            "engagement_potential": "low|medium|high",
            "accessibility_score": "poor|fair|good|excellent",
            "content_type": "informational|promotional|instructional|entertainment",
            "tone": "formal|casual|friendly|professional|technical",
            "improvements": ["improvement1", "improvement2"],
            "strengths": ["strength1", "strength2"]
        }}
        """
    
    @staticmethod
    def responsive_design_analysis(css_content: str, html_structure: Dict[str, Any]) -> str:
        """Prompt for analyzing responsive design implementation"""
        return f"""
        Analyze the responsive design implementation of this website.
        
        CSS Content Sample: "{css_content[:500]}{'...' if len(css_content) > 500 else ''}"
        HTML Structure: {html_structure}
        
        Evaluate:
        1. Mobile responsiveness
        2. Breakpoint strategy
        3. Layout adaptation methods
        4. Touch-friendly elements
        5. Performance on different devices
        
        Return JSON:
        {{
            "mobile_friendly": true/false,
            "breakpoints": ["320px", "768px", "1024px"],
            "layout_method": "flexbox|grid|float|table|mixed",
            "responsive_images": true/false,
            "touch_optimization": "none|basic|advanced",
            "viewport_configured": true/false,
            "responsive_score": "poor|fair|good|excellent",
            "issues": ["issue1", "issue2"],
            "recommendations": ["rec1", "rec2"]
        }}
        """
    
    @staticmethod
    def performance_analysis(file_sizes: Dict[str, int], asset_counts: Dict[str, int]) -> str:
        """Prompt for analyzing website performance characteristics"""
        return f"""
        Analyze the performance characteristics of this website.
        
        File Sizes: {file_sizes}
        Asset Counts: {asset_counts}
        
        Evaluate:
        1. Page load performance
        2. Asset optimization
        3. Resource usage
        4. Caching opportunities
        5. Performance bottlenecks
        
        Return JSON:
        {{
            "estimated_load_time": "fast|moderate|slow|very_slow",
            "total_size_mb": 0.0,
            "largest_assets": ["asset1", "asset2"],
            "optimization_opportunities": ["compress_images", "minify_css", "etc"],
            "critical_issues": ["issue1", "issue2"],
            "performance_score": "poor|fair|good|excellent",
            "mobile_performance": "poor|fair|good|excellent",
            "recommendations": ["rec1", "rec2"]
        }}
        """