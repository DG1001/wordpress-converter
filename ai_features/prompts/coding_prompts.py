"""
Coding Prompts

Templates for code generation and modification tasks.
"""

from typing import Dict, Any, List


class CodingPrompts:
    """Collection of coding prompt templates"""
    
    @staticmethod
    def html_modification(file_path: str, target_content: str, modification_goal: str, context: Dict[str, Any]) -> str:
        """Prompt for HTML content modification"""
        return f"""
        You are an expert web developer. Modify the HTML content in this file.
        
        File: {file_path}
        Target Content to Modify: "{target_content}"
        Goal: {modification_goal}
        
        Context:
        {context}
        
        Requirements:
        1. Maintain valid HTML structure
        2. Preserve existing functionality 
        3. Keep semantic markup
        4. Ensure accessibility compliance
        5. Maintain responsive design
        
        Provide the exact replacement content that should replace the target content.
        Only return the new HTML content, no explanations.
        
        Considerations:
        - Preserve class names and IDs unless specifically changing them
        - Maintain proper heading hierarchy
        - Keep alt text for images
        - Ensure form elements have proper labels
        - Use semantic HTML5 elements where appropriate
        
        New HTML content:
        """
    
    @staticmethod
    def css_styling(target_selector: str, modification_goal: str, existing_styles: str, context: Dict[str, Any]) -> str:
        """Prompt for CSS styling modifications"""
        return f"""
        You are an expert CSS developer. Create or modify CSS styles.
        
        Target Selector: {target_selector}
        Goal: {modification_goal}
        Existing Styles: "{existing_styles}"
        
        Context:
        {context}
        
        Requirements:
        1. Write clean, maintainable CSS
        2. Ensure cross-browser compatibility
        3. Maintain responsive design
        4. Follow CSS best practices
        5. Optimize for performance
        
        Provide complete CSS rules for the target selector.
        Include responsive breakpoints if needed.
        
        Considerations:
        - Use modern CSS features where appropriate (flexbox, grid, custom properties)
        - Ensure proper specificity without !important unless necessary
        - Include vendor prefixes for older browser support
        - Consider dark mode compatibility
        - Optimize for accessibility (contrast, focus states)
        
        CSS code:
        ```css
        """
    
    @staticmethod
    def javascript_functionality(functionality_goal: str, existing_code: str, context: Dict[str, Any]) -> str:
        """Prompt for JavaScript functionality implementation"""
        return f"""
        You are an expert JavaScript developer. Implement the requested functionality.
        
        Goal: {functionality_goal}
        Existing Code: "{existing_code}"
        
        Context:
        {context}
        
        Requirements:
        1. Write modern, clean JavaScript (ES6+)
        2. Ensure cross-browser compatibility
        3. Handle errors gracefully
        4. Follow best practices and patterns
        5. Optimize for performance
        
        Provide complete JavaScript code.
        Include proper error handling and edge cases.
        
        Considerations:
        - Use const/let instead of var
        - Implement proper event handling
        - Consider mobile touch events
        - Ensure accessibility for keyboard navigation
        - Add appropriate comments for complex logic
        - Use modern APIs where supported with fallbacks
        
        JavaScript code:
        ```javascript
        """
    
    @staticmethod
    def responsive_design_implementation(breakpoints: List[str], layout_goal: str, existing_css: str) -> str:
        """Prompt for responsive design implementation"""
        return f"""
        You are an expert in responsive web design. Implement responsive layout.
        
        Target Breakpoints: {breakpoints}
        Layout Goal: {layout_goal}
        Existing CSS: "{existing_css}"
        
        Requirements:
        1. Mobile-first approach
        2. Smooth transitions between breakpoints
        3. Optimal user experience on all devices
        4. Performance optimization
        5. Touch-friendly interface elements
        
        Provide complete responsive CSS with media queries.
        
        Considerations:
        - Use relative units (rem, em, %, vw, vh) where appropriate
        - Implement flexible grid systems
        - Ensure readable font sizes on all devices
        - Optimize touch targets (minimum 44px)
        - Consider landscape and portrait orientations
        - Test on various screen densities
        
        Responsive CSS:
        ```css
        """
    
    @staticmethod
    def accessibility_improvement(element_html: str, accessibility_goal: str, current_issues: List[str]) -> str:
        """Prompt for accessibility improvements"""
        return f"""
        You are an expert in web accessibility (WCAG 2.1). Improve the accessibility of this HTML.
        
        Current HTML: "{element_html}"
        Goal: {accessibility_goal}
        Current Issues: {current_issues}
        
        Requirements:
        1. Follow WCAG 2.1 AA guidelines
        2. Ensure keyboard navigation
        3. Provide proper screen reader support
        4. Maintain visual design integrity
        5. Test with accessibility tools
        
        Provide the improved HTML with proper accessibility attributes.
        
        Considerations:
        - Add proper ARIA labels and roles
        - Ensure sufficient color contrast
        - Implement focus management
        - Provide alternative text for images
        - Use semantic HTML elements
        - Add skip links for navigation
        - Ensure form labels are properly associated
        
        Accessible HTML:
        ```html
        """
    
    @staticmethod
    def performance_optimization(code_type: str, current_code: str, performance_goal: str) -> str:
        """Prompt for performance optimization"""
        return f"""
        You are an expert in web performance optimization. Optimize this {code_type} code.
        
        Current Code: "{current_code}"
        Performance Goal: {performance_goal}
        
        Requirements:
        1. Minimize file size and load time
        2. Optimize rendering performance
        3. Reduce network requests
        4. Improve Core Web Vitals
        5. Maintain functionality
        
        Provide optimized code with explanatory comments for major changes.
        
        Optimization Strategies:
        - Minimize and compress code
        - Use efficient selectors (CSS)
        - Implement lazy loading where appropriate
        - Optimize images and assets
        - Remove unused code
        - Use modern, efficient APIs
        - Consider caching strategies
        
        Optimized {code_type}:
        ```{code_type.lower()}
        """
    
    @staticmethod
    def component_creation(component_type: str, requirements: Dict[str, Any], design_system: Dict[str, Any]) -> str:
        """Prompt for creating reusable components"""
        return f"""
        You are an expert in component-based web development. Create a reusable {component_type} component.
        
        Requirements: {requirements}
        Design System: {design_system}
        
        Component Specifications:
        1. Self-contained and reusable
        2. Configurable through parameters
        3. Accessible and semantic
        4. Responsive and mobile-friendly
        5. Consistent with design system
        
        Provide complete HTML, CSS, and JavaScript for the component.
        
        Considerations:
        - Use semantic HTML structure
        - Implement proper state management
        - Add configuration options
        - Include error handling
        - Follow naming conventions
        - Document usage examples
        
        Component Code:
        
        HTML:
        ```html
        """
    
    @staticmethod
    def integration_implementation(integration_type: str, api_details: Dict[str, Any], security_requirements: List[str]) -> str:
        """Prompt for third-party integration implementation"""
        return f"""
        You are an expert in web integrations and APIs. Implement {integration_type} integration.
        
        API Details: {api_details}
        Security Requirements: {security_requirements}
        
        Implementation Requirements:
        1. Secure API communication
        2. Proper error handling
        3. User feedback and loading states
        4. Rate limiting consideration
        5. Data validation and sanitization
        
        Provide complete integration code with proper security measures.
        
        Security Considerations:
        - Validate all input data
        - Sanitize output data
        - Use HTTPS for all communications
        - Implement proper authentication
        - Handle API errors gracefully
        - Protect against XSS and CSRF
        - Follow OWASP guidelines
        
        Integration Code:
        ```javascript
        """
    
    @staticmethod
    def form_enhancement(form_html: str, enhancement_goal: str, validation_requirements: List[str]) -> str:
        """Prompt for form functionality enhancement"""
        return f"""
        You are an expert in form development and user experience. Enhance this form.
        
        Current Form HTML: "{form_html}"
        Enhancement Goal: {enhancement_goal}
        Validation Requirements: {validation_requirements}
        
        Requirements:
        1. Improve user experience
        2. Implement proper validation
        3. Ensure accessibility
        4. Add helpful user feedback
        5. Optimize for mobile devices
        
        Provide enhanced HTML, CSS, and JavaScript for the form.
        
        Enhancement Areas:
        - Client-side validation with helpful messages
        - Progressive enhancement
        - Keyboard navigation support
        - Touch-friendly mobile interface
        - Loading and success states
        - Error handling and recovery
        - Autocomplete and accessibility features
        
        Enhanced Form:
        
        HTML:
        ```html
        """
    
    @staticmethod
    def animation_implementation(animation_goal: str, target_elements: List[str], performance_budget: str) -> str:
        """Prompt for animation and interaction implementation"""
        return f"""
        You are an expert in web animations and micro-interactions. Implement engaging animations.
        
        Animation Goal: {animation_goal}
        Target Elements: {target_elements}
        Performance Budget: {performance_budget}
        
        Requirements:
        1. Smooth, performant animations
        2. Respect user preferences (prefers-reduced-motion)
        3. Enhance user experience without being distracting
        4. Optimize for 60fps performance
        5. Provide meaningful feedback
        
        Provide CSS and/or JavaScript for the animations.
        
        Animation Principles:
        - Use transform and opacity for smooth animations
        - Implement easing functions for natural motion
        - Consider animation duration and timing
        - Add hover and focus states
        - Respect accessibility preferences
        - Use hardware acceleration where appropriate
        - Test on various devices and browsers
        
        Animation Code:
        
        CSS:
        ```css
        """
    
    @staticmethod
    def cross_browser_compatibility(code: str, browser_requirements: List[str], fallback_strategy: str) -> str:
        """Prompt for cross-browser compatibility implementation"""
        return f"""
        You are an expert in cross-browser web development. Ensure compatibility across browsers.
        
        Current Code: "{code}"
        Browser Requirements: {browser_requirements}
        Fallback Strategy: {fallback_strategy}
        
        Compatibility Requirements:
        1. Support specified browsers and versions
        2. Implement graceful degradation
        3. Use progressive enhancement
        4. Test modern features with fallbacks
        5. Ensure consistent user experience
        
        Provide cross-browser compatible code with appropriate fallbacks.
        
        Compatibility Strategies:
        - Feature detection over browser detection
        - Polyfills for missing functionality
        - Vendor prefixes where needed
        - Graceful degradation for older browsers
        - Progressive enhancement for modern features
        - Consistent styling across browsers
        - Thorough testing procedures
        
        Compatible Code:
        """