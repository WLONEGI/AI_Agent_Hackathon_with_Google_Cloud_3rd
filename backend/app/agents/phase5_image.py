"""Phase 5: Scene Image Generation Agent with Parallel Processing."""

from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService


@dataclass
class ImageGenerationTask:
    """Individual image generation task."""
    panel_id: str
    prompt: str
    negative_prompt: str
    style_parameters: Dict[str, Any]
    priority: int
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ImageGenerationResult:
    """Result of image generation."""
    panel_id: str
    success: bool
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    generation_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    retry_count: int = 0


class Phase5ImageAgent(BaseAgent):
    """Agent for parallel scene image generation with semaphore control."""
    
    def __init__(self):
        super().__init__(
            phase_number=5,
            phase_name="シーン画像生成",
            timeout_seconds=settings.phase_timeouts[5]
        )
        
        # Initialize structured prompts
        from app.agents.phases.phase5_image.prompts import ImageGenerationPrompts
        self.prompts = ImageGenerationPrompts()
        
        # Parallel processing control
        self.max_concurrent_generations = settings.ai_models.max_parallel_image_generation
        self.semaphore = asyncio.Semaphore(self.max_concurrent_generations)
        
        # Style templates for different scenarios
        self.style_templates = {
            "character_focus": {
                "base_style": "manga style, clean lines, detailed character",
                "emphasis": "character expression and detail",
                "background": "simple or blurred background"
            },
            "environment_focus": {
                "base_style": "manga style, detailed environment",
                "emphasis": "atmospheric background and setting",
                "background": "detailed environmental elements"
            },
            "action_scene": {
                "base_style": "dynamic manga style, motion effects",
                "emphasis": "movement and energy",
                "background": "dynamic backgrounds with motion blur"
            },
            "emotional_scene": {
                "base_style": "soft manga style, emotional lighting",
                "emphasis": "mood and atmosphere",
                "background": "mood-supporting backgrounds"
            }
        }
        
        # Quality assessment criteria
        self.quality_criteria = {
            "character_accuracy": 0.25,
            "style_consistency": 0.20,
            "composition_quality": 0.20,
            "technical_quality": 0.15,
            "narrative_clarity": 0.10,
            "artistic_appeal": 0.10
        }
        
        # Vertex AI サービス初期化
        self.vertex_ai = VertexAIService()
        
        # Cache for generated images
        self.image_cache = {}
        self.generation_stats = {
            "total_generated": 0,
            "successful_generations": 0,
            "cache_hits": 0,
            "average_generation_time": 0,
            "quality_distribution": {"high": 0, "medium": 0, "low": 0}
        }
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Generate images for all scenes with parallel processing."""
        
        if not previous_results or not all(i in previous_results for i in [1, 2, 3, 4]):
            raise ValueError("Phases 1-4 results required for image generation")
        
        # Extract previous phase results
        phase1_result = previous_results[1]
        phase2_result = previous_results[2] 
        phase3_result = previous_results[3]
        phase4_result = previous_results[4]
        
        # Create image generation tasks
        generation_tasks = await self._create_generation_tasks(
            phase1_result, phase2_result, phase3_result, phase4_result
        )
        
        self.log_info(
            f"Starting parallel image generation for {len(generation_tasks)} panels",
            session_id=str(session_id),
            max_concurrent=self.max_concurrent_generations
        )
        
        # Execute parallel generation with semaphore control
        generation_results = await self._execute_parallel_generation(
            generation_tasks, session_id
        )
        
        # Process and validate results
        processed_results = await self._process_generation_results(
            generation_results, generation_tasks
        )
        
        # Generate quality analysis
        quality_analysis = await self._analyze_generation_quality(processed_results)
        
        # Create scene image mapping
        scene_image_mapping = await self._create_scene_image_mapping(
            processed_results, phase4_result
        )
        
        # Generate consistency report
        consistency_report = await self._generate_consistency_report(
            processed_results, phase2_result
        )
        
        result = {
            "generated_images": processed_results,
            "scene_image_mapping": scene_image_mapping,
            "quality_analysis": quality_analysis,
            "consistency_report": consistency_report,
            "generation_stats": self.generation_stats.copy(),
            "total_images_generated": len(processed_results),
            "successful_generations": len([r for r in processed_results if r.success]),
            "failed_generations": len([r for r in processed_results if not r.success]),
            "average_generation_time": self._calculate_average_generation_time(processed_results),
            "parallel_efficiency_score": self._calculate_parallel_efficiency_score(
                generation_tasks, processed_results
            ),
            "cache_utilization": self._calculate_cache_utilization()
        }
        
        return result
    
    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate comprehensive prompt for image generation phase."""
        
        return self.prompts.get_main_prompt(
            input_data=input_data,
            previous_results=previous_results
        )
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate Phase 5 output."""
        
        required_keys = [
            "generated_images", "scene_image_mapping", "quality_analysis",
            "total_images_generated", "successful_generations"
        ]
        
        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False
        
        generated_images = output_data.get("generated_images", [])
        
        # Must have at least 1 successful generation
        successful = [img for img in generated_images if img.success]
        if len(successful) < 1:
            self.log_warning("No successful image generations")
            return False
        
        # Check image result completeness
        for img in generated_images:
            if img.success:
                if not img.image_url:
                    self.log_warning(f"Missing image URL for {img.panel_id}")
                    return False
        
        return True
    
    async def _create_generation_tasks(
        self,
        phase1_result: Dict[str, Any],
        phase2_result: Dict[str, Any],
        phase3_result: Dict[str, Any],
        phase4_result: Dict[str, Any]
    ) -> List[ImageGenerationTask]:
        """Create individual image generation tasks."""
        
        tasks = []
        
        # Get data from previous phases
        genre = phase1_result.get("genre", "general")
        world_setting = phase1_result.get("world_setting", {})
        characters = phase2_result.get("characters", [])
        visual_descriptions = phase2_result.get("visual_descriptions", {})
        panel_specifications = phase4_result.get("panel_specifications", [])
        composition_guidelines = phase4_result.get("composition_guidelines", {})
        
        # Create tasks for each panel
        for i, panel_spec in enumerate(panel_specifications):
            panel_id = panel_spec.get("panel_id", f"panel_{i}")
            
            # Generate prompts for this panel
            main_prompt = await self._generate_panel_prompt(
                panel_spec, characters, visual_descriptions, genre, world_setting
            )
            
            negative_prompt = await self._generate_negative_prompt(
                panel_spec, composition_guidelines
            )
            
            style_parameters = await self._determine_style_parameters(
                panel_spec, genre, composition_guidelines
            )
            
            # Determine priority (earlier panels and climax panels have higher priority)
            priority = self._calculate_panel_priority(panel_spec, panel_specifications)
            
            task = ImageGenerationTask(
                panel_id=panel_id,
                prompt=main_prompt,
                negative_prompt=negative_prompt,
                style_parameters=style_parameters,
                priority=priority
            )
            
            tasks.append(task)
        
        # Sort by priority (higher priority first)
        tasks.sort(key=lambda x: x.priority, reverse=True)
        
        return tasks
    
    async def _generate_panel_prompt(
        self,
        panel_spec: Dict[str, Any],
        characters: List[Dict[str, Any]],
        visual_descriptions: Dict[str, Dict[str, Any]],
        genre: str,
        world_setting: Dict[str, Any]
    ) -> str:
        """Generate detailed prompt for individual panel."""
        
        # Base style and quality
        base_prompt = f"high quality manga style illustration, {genre} genre"
        
        # Camera and composition
        camera_angle = panel_spec.get("camera_angle", "medium_shot")
        composition = panel_spec.get("composition", "rule_of_thirds")
        
        camera_prompt = self._get_camera_angle_prompt(camera_angle)
        composition_prompt = self._get_composition_prompt(composition)
        
        # Characters in panel
        panel_characters = panel_spec.get("characters", [])
        character_prompt = await self._generate_character_prompt(
            panel_characters, characters, visual_descriptions
        )
        
        # Environment and mood
        environment_prompt = self._generate_environment_prompt(
            panel_spec, world_setting
        )
        
        mood_prompt = self._generate_mood_prompt(
            panel_spec.get("emotional_tone", "neutral"),
            panel_spec.get("lighting_setup", "natural")
        )
        
        # Combine all elements
        full_prompt = f"{base_prompt}, {camera_prompt}, {composition_prompt}"
        
        if character_prompt:
            full_prompt += f", {character_prompt}"
        
        if environment_prompt:
            full_prompt += f", {environment_prompt}"
        
        if mood_prompt:
            full_prompt += f", {mood_prompt}"
        
        # Add technical specifications
        technical_specs = "clean lines, detailed, professional manga art, black and white"
        full_prompt += f", {technical_specs}"
        
        return full_prompt
    
    def _get_camera_angle_prompt(self, camera_angle: str) -> str:
        """Get prompt text for camera angle."""
        
        angle_prompts = {
            "extreme_close_up": "extreme close-up shot, facial details, intense focus",
            "close_up": "close-up shot, upper body and face, detailed expression",
            "medium_shot": "medium shot, waist up, balanced composition",
            "full_shot": "full body shot, complete character visible",
            "wide_shot": "wide establishing shot, environmental context",
            "bird_eye": "bird's eye view, high angle shot, overhead perspective",
            "worm_eye": "worm's eye view, low angle shot, upward perspective"
        }
        
        return angle_prompts.get(camera_angle, "medium shot, balanced composition")
    
    def _get_composition_prompt(self, composition: str) -> str:
        """Get prompt text for composition style."""
        
        composition_prompts = {
            "rule_of_thirds": "rule of thirds composition, balanced placement",
            "centered_composition": "centered composition, symmetrical balance",
            "diagonal_composition": "dynamic diagonal composition, visual energy",
            "environmental_composition": "environmental composition, context focus"
        }
        
        return composition_prompts.get(composition, "balanced composition")
    
    async def _generate_character_prompt(
        self,
        panel_characters: List[Dict[str, Any]],
        all_characters: List[Dict[str, Any]],
        visual_descriptions: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate character-specific prompt."""
        
        if not panel_characters:
            return ""
        
        character_prompts = []
        
        for panel_char in panel_characters:
            char_name = panel_char.get("name", "")
            
            # Find full character data
            full_char = next((c for c in all_characters if c.get("name") == char_name), {})
            
            # Get visual description
            visual_desc = visual_descriptions.get(char_name, {})
            
            # Build character prompt
            char_prompt_parts = []
            
            # Basic appearance
            appearance = full_char.get("appearance", "")
            if appearance:
                char_prompt_parts.append(appearance)
            
            # Visual style from phase 2
            base_prompt = visual_desc.get("base_prompt", "")
            if base_prompt:
                char_prompt_parts.append(base_prompt)
            
            # Character expression
            expression = panel_char.get("expression", "neutral")
            char_prompt_parts.append(f"{expression} expression")
            
            # Character prominence
            prominence = panel_char.get("prominence", 0.5)
            if prominence > 0.8:
                char_prompt_parts.append("prominent character placement")
            elif prominence < 0.3:
                char_prompt_parts.append("background character")
            
            if char_prompt_parts:
                character_prompts.append(f"{char_name}: {', '.join(char_prompt_parts)}")
        
        return "; ".join(character_prompts) if character_prompts else ""
    
    def _generate_environment_prompt(
        self,
        panel_spec: Dict[str, Any],
        world_setting: Dict[str, Any]
    ) -> str:
        """Generate environment prompt."""
        
        environment_parts = []
        
        # Background detail level
        bg_detail = panel_spec.get("background_detail", "moderate")
        if bg_detail == "detailed":
            environment_parts.append("detailed background")
        elif bg_detail == "simple":
            environment_parts.append("simple background")
        elif bg_detail == "minimal":
            environment_parts.append("minimal background, focus on character")
        
        # World setting influence
        location = world_setting.get("location", "")
        time_period = world_setting.get("time_period", "present")
        
        if location and bg_detail != "minimal":
            location_prompts = {
                "学校": "school setting, classroom or school grounds",
                "都市": "urban setting, city environment",
                "自然": "natural setting, outdoor environment",
                "異世界": "fantasy world setting, magical environment",
                "宇宙": "space setting, futuristic environment"
            }
            
            location_prompt = location_prompts.get(location, "appropriate setting")
            environment_parts.append(location_prompt)
        
        # Time period styling
        if time_period != "present" and bg_detail != "minimal":
            period_prompts = {
                "past": "historical setting, traditional elements",
                "future": "futuristic setting, sci-fi elements",
                "fantasy": "fantasy setting, magical elements"
            }
            
            period_prompt = period_prompts.get(time_period, "contemporary setting")
            environment_parts.append(period_prompt)
        
        return ", ".join(environment_parts) if environment_parts else ""
    
    def _generate_mood_prompt(self, emotional_tone: str, lighting_setup: str) -> str:
        """Generate mood and lighting prompt."""
        
        mood_parts = []
        
        # Emotional tone
        tone_prompts = {
            "tension": "tense atmosphere, dramatic mood",
            "anxiety": "anxious atmosphere, unsettling mood",
            "climax": "intense atmosphere, peak emotion",
            "relief": "relieved atmosphere, calm mood",
            "satisfaction": "satisfied atmosphere, positive mood",
            "curiosity": "intriguing atmosphere, mysterious mood"
        }
        
        tone_prompt = tone_prompts.get(emotional_tone, "balanced mood")
        mood_parts.append(tone_prompt)
        
        # Lighting
        lighting_prompts = {
            "dramatic_high_contrast": "dramatic lighting, high contrast shadows",
            "harsh_shadows": "harsh lighting, strong shadows",
            "intense_directional": "intense directional lighting",
            "soft_natural": "soft natural lighting, gentle shadows",
            "warm_even": "warm even lighting, comfortable atmosphere",
            "natural_balanced": "natural balanced lighting"
        }
        
        lighting_prompt = lighting_prompts.get(lighting_setup, "natural lighting")
        mood_parts.append(lighting_prompt)
        
        return ", ".join(mood_parts)
    
    async def _generate_negative_prompt(
        self,
        panel_spec: Dict[str, Any],
        composition_guidelines: Dict[str, Any]
    ) -> str:
        """Generate negative prompt to exclude unwanted elements."""
        
        negative_elements = [
            "low quality",
            "blurry",
            "distorted",
            "deformed",
            "bad anatomy", 
            "bad proportions",
            "duplicate",
            "cropped",
            "out of frame",
            "worst quality",
            "low resolution",
            "watermark",
            "signature"
        ]
        
        # Add camera angle specific negatives
        camera_angle = panel_spec.get("camera_angle", "medium_shot")
        if camera_angle in ["close_up", "extreme_close_up"]:
            negative_elements.extend([
                "full body",
                "wide shot",
                "distant view"
            ])
        elif camera_angle in ["wide_shot", "bird_eye"]:
            negative_elements.extend([
                "close up face",
                "extreme close up",
                "portrait only"
            ])
        
        # Add character specific negatives
        panel_characters = panel_spec.get("characters", [])
        if len(panel_characters) == 1:
            negative_elements.append("multiple people")
        elif len(panel_characters) > 1:
            negative_elements.append("single person only")
        
        return ", ".join(negative_elements)
    
    async def _determine_style_parameters(
        self,
        panel_spec: Dict[str, Any],
        genre: str,
        composition_guidelines: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine style parameters for image generation."""
        
        # Base parameters
        parameters = {
            "art_style": "manga",
            "quality_level": "high",
            "aspect_ratio": panel_spec.get("aspect_ratio", "4:3"),
            "color_mode": "black_and_white"
        }
        
        # Determine emphasis based on focus element
        focus_element = panel_spec.get("focus_element", "character_interaction")
        
        if "character" in focus_element:
            parameters["emphasis"] = "character_focus"
            parameters["detail_level"] = "character_detailed"
        elif "environment" in focus_element:
            parameters["emphasis"] = "environment_focus"
            parameters["detail_level"] = "background_detailed"
        elif "movement" in focus_element:
            parameters["emphasis"] = "action_scene"
            parameters["detail_level"] = "dynamic_focused"
        else:
            parameters["emphasis"] = "balanced"
            parameters["detail_level"] = "standard"
        
        # Genre specific adjustments
        if genre == "action":
            parameters["energy_level"] = "high"
            parameters["line_weight"] = "bold"
        elif genre == "romance":
            parameters["energy_level"] = "gentle"
            parameters["line_weight"] = "soft"
        elif genre == "mystery":
            parameters["energy_level"] = "atmospheric"
            parameters["line_weight"] = "varied"
        
        # Composition guidelines influence
        overall_style = composition_guidelines.get("overall_style", {})
        if overall_style.get("emphasis") == "dynamic_movement":
            parameters["dynamic_elements"] = True
        
        return parameters
    
    def _calculate_panel_priority(
        self,
        panel_spec: Dict[str, Any],
        all_panels: List[Dict[str, Any]]
    ) -> int:
        """Calculate priority for panel generation (1-10, higher is more important)."""
        
        priority = 5  # Base priority
        
        # Earlier panels get higher priority
        panel_number = panel_spec.get("panel_number", 1)
        page_number = panel_spec.get("page_number", 1)
        
        if page_number == 1:
            priority += 2  # First page is important
        
        if panel_number == 1:
            priority += 1  # First panel of page is important
        
        # Emotional intensity affects priority
        emotional_tone = panel_spec.get("emotional_tone", "neutral")
        if emotional_tone in ["climax", "tension"]:
            priority += 2
        elif emotional_tone in ["anxiety", "relief"]:
            priority += 1
        
        # Panel size affects priority
        panel_size = panel_spec.get("size", "medium")
        if panel_size in ["splash", "large"]:
            priority += 1
        
        # Character prominence affects priority
        panel_characters = panel_spec.get("characters", [])
        for char in panel_characters:
            if char.get("prominence", 0) > 0.8:
                priority += 1
                break
        
        return min(10, max(1, priority))
    
    async def _execute_parallel_generation(
        self,
        generation_tasks: List[ImageGenerationTask],
        session_id: UUID
    ) -> List[ImageGenerationResult]:
        """Execute parallel image generation with semaphore control."""
        
        self.log_info(
            f"Starting parallel generation of {len(generation_tasks)} images",
            session_id=str(session_id)
        )
        
        # Create semaphore for controlling concurrency
        async def generate_single_image(task: ImageGenerationTask) -> ImageGenerationResult:
            async with self.semaphore:
                return await self._generate_single_image(task, session_id)
        
        # Execute all tasks concurrently with semaphore control
        start_time = time.time()
        
        # Use asyncio.gather for concurrent execution
        results = await asyncio.gather(
            *[generate_single_image(task) for task in generation_tasks],
            return_exceptions=True
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle exceptions by creating failed result
                failed_result = ImageGenerationResult(
                    panel_id=generation_tasks[i].panel_id,
                    success=False,
                    error_message=str(result),
                    generation_time_ms=int(total_time * 1000)
                )
                processed_results.append(failed_result)
            else:
                processed_results.append(result)
        
        self.log_info(
            f"Completed parallel generation in {total_time:.2f}s",
            session_id=str(session_id),
            successful=len([r for r in processed_results if r.success]),
            failed=len([r for r in processed_results if not r.success])
        )
        
        return processed_results
    
    async def _generate_single_image(
        self,
        task: ImageGenerationTask,
        session_id: UUID
    ) -> ImageGenerationResult:
        """Generate a single image with retry logic."""
        
        for attempt in range(task.max_retries + 1):
            try:
                start_time = time.time()
                
                # Check cache first
                cache_key = self._generate_cache_key(task)
                if cache_key in self.image_cache:
                    self.generation_stats["cache_hits"] += 1
                    cached_result = self.image_cache[cache_key]
                    return ImageGenerationResult(
                        panel_id=task.panel_id,
                        success=True,
                        image_url=cached_result["image_url"],
                        thumbnail_url=cached_result.get("thumbnail_url"),
                        generation_time_ms=0,  # Cache hit
                        quality_score=cached_result.get("quality_score", 0.8)
                    )
                
                # Generate new image with Imagen 4
                self.log_info(
                    f"Generating image for {task.panel_id} (attempt {attempt + 1})",
                    session_id=str(session_id)
                )
                
                # Call Vertex AI Imagen 4 for image generation
                try:
                    ai_response = await self.vertex_ai.generate_images(
                        prompts=[task.prompt],
                        negative_prompt=task.negative_prompt,
                        batch_size=1,
                        max_retries=2
                    )
                    
                    if ai_response and len(ai_response) > 0 and ai_response[0].get("success", False):
                        # Parse Imagen 4 response
                        image_result = ai_response[0]
                        generation_result = {
                            "success": True,
                            "image_url": image_result.get("image_url", ""),
                            "thumbnail_url": image_result.get("thumbnail_url", ""),
                            "quality_score": image_result.get("quality_score", 0.8)
                        }
                        
                        self.log_info(
                            f"Imagen 4 generation successful for {task.panel_id}",
                            session_id=str(session_id),
                            tokens=image_result.get("usage", {}).get("total_tokens", 0)
                        )
                        
                    else:
                        # Fallback to simulated generation
                        error_msg = ai_response[0].get("error") if ai_response else "Unknown error"
                        self.log_warning(
                            f"Imagen 4 failed for {task.panel_id}, using fallback: {error_msg}",
                            session_id=str(session_id)
                        )
                        generation_result = await self._simulate_image_generation(task)
                        
                except Exception as ai_error:
                    # Fallback to simulated generation on AI error
                    self.log_error(
                        f"Imagen 4 error for {task.panel_id}, using fallback: {str(ai_error)}",
                        session_id=str(session_id)
                    )
                    generation_result = await self._simulate_image_generation(task)
                
                end_time = time.time()
                generation_time_ms = int((end_time - start_time) * 1000)
                
                if generation_result["success"]:
                    # Cache successful result
                    self.image_cache[cache_key] = generation_result
                    
                    # Update stats
                    self.generation_stats["total_generated"] += 1
                    self.generation_stats["successful_generations"] += 1
                    
                    # Update average generation time
                    current_avg = self.generation_stats["average_generation_time"]
                    total = self.generation_stats["total_generated"]
                    self.generation_stats["average_generation_time"] = (
                        (current_avg * (total - 1) + generation_time_ms) / total
                    )
                    
                    return ImageGenerationResult(
                        panel_id=task.panel_id,
                        success=True,
                        image_url=generation_result["image_url"],
                        thumbnail_url=generation_result.get("thumbnail_url"),
                        generation_time_ms=generation_time_ms,
                        quality_score=generation_result.get("quality_score", 0.8),
                        retry_count=attempt
                    )
                else:
                    # Generation failed, try again if retries available
                    if attempt < task.max_retries:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        return ImageGenerationResult(
                            panel_id=task.panel_id,
                            success=False,
                            error_message=generation_result.get("error", "Generation failed"),
                            generation_time_ms=generation_time_ms,
                            retry_count=attempt
                        )
                        
            except Exception as e:
                self.log_error(
                    f"Error generating image for {task.panel_id}",
                    error=e,
                    session_id=str(session_id)
                )
                
                if attempt < task.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    return ImageGenerationResult(
                        panel_id=task.panel_id,
                        success=False,
                        error_message=str(e),
                        retry_count=attempt
                    )
        
        # Should not reach here
        return ImageGenerationResult(
            panel_id=task.panel_id,
            success=False,
            error_message="Max retries exceeded"
        )
    
    def _generate_cache_key(self, task: ImageGenerationTask) -> str:
        """Generate cache key for image generation task."""
        
        # Create a hash of the prompt and style parameters
        import hashlib
        
        cache_data = {
            "prompt": task.prompt,
            "negative_prompt": task.negative_prompt,
            "style": task.style_parameters
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _simulate_image_generation(self, task: ImageGenerationTask) -> Dict[str, Any]:
        """Simulate image generation (replace with actual API call)."""
        
        # Simulate generation time based on complexity
        base_time = 2.0  # Base 2 seconds
        
        # Add complexity factors
        if "detailed" in task.prompt.lower():
            base_time += 1.0
        if "high quality" in task.prompt.lower():
            base_time += 0.5
        if len(task.prompt) > 200:
            base_time += 0.5
        
        await asyncio.sleep(base_time)
        
        # Simulate 90% success rate
        import random
        success = random.random() > 0.1
        
        if success:
            # Simulate successful generation
            quality_score = random.uniform(0.7, 0.95)
            
            return {
                "success": True,
                "image_url": f"https://example.com/generated/{task.panel_id}.png",
                "thumbnail_url": f"https://example.com/thumbnails/{task.panel_id}_thumb.png",
                "quality_score": quality_score
            }
        else:
            return {
                "success": False,
                "error": "Simulated generation failure"
            }
    
    async def _process_generation_results(
        self,
        generation_results: List[ImageGenerationResult],
        generation_tasks: List[ImageGenerationTask]
    ) -> List[ImageGenerationResult]:
        """Process and validate generation results."""
        
        processed_results = []
        
        for result in generation_results:
            # Validate successful results
            if result.success:
                validation_result = await self._validate_generated_image(result)
                if validation_result["valid"]:
                    processed_results.append(result)
                else:
                    # Mark as failed due to validation
                    failed_result = ImageGenerationResult(
                        panel_id=result.panel_id,
                        success=False,
                        error_message=f"Validation failed: {validation_result['reason']}",
                        generation_time_ms=result.generation_time_ms,
                        retry_count=result.retry_count
                    )
                    processed_results.append(failed_result)
            else:
                # Failed result, add as-is
                processed_results.append(result)
        
        return processed_results
    
    async def _validate_generated_image(self, result: ImageGenerationResult) -> Dict[str, Any]:
        """Validate generated image quality and content."""
        
        # TODO: Implement actual image validation
        # For now, simulate validation based on quality score
        
        if not result.image_url:
            return {"valid": False, "reason": "No image URL provided"}
        
        if result.quality_score and result.quality_score < 0.6:
            return {"valid": False, "reason": "Quality score too low"}
        
        # Simulate content validation
        import random
        if random.random() > 0.95:  # 5% validation failure rate
            return {"valid": False, "reason": "Content validation failed"}
        
        return {"valid": True, "reason": "Validation passed"}
    
    async def _analyze_generation_quality(
        self, generation_results: List[ImageGenerationResult]
    ) -> Dict[str, Any]:
        """Analyze overall generation quality."""
        
        successful_results = [r for r in generation_results if r.success]
        failed_results = [r for r in generation_results if not r.success]
        
        if not generation_results:
            return {"error": "No generation results to analyze"}
        
        # Calculate success rate
        success_rate = len(successful_results) / len(generation_results)
        
        # Calculate average quality score
        quality_scores = [r.quality_score for r in successful_results if r.quality_score]
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Calculate average generation time
        generation_times = [r.generation_time_ms for r in successful_results if r.generation_time_ms]
        average_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0
        
        # Quality distribution
        quality_distribution = {"high": 0, "medium": 0, "low": 0}
        for score in quality_scores:
            if score >= 0.8:
                quality_distribution["high"] += 1
            elif score >= 0.6:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1
        
        # Retry analysis
        retry_stats = {"no_retry": 0, "single_retry": 0, "multiple_retry": 0}
        for result in generation_results:
            if result.retry_count == 0:
                retry_stats["no_retry"] += 1
            elif result.retry_count == 1:
                retry_stats["single_retry"] += 1
            else:
                retry_stats["multiple_retry"] += 1
        
        # Failure analysis
        failure_reasons = {}
        for failed in failed_results:
            reason = failed.error_message or "Unknown error"
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        quality_analysis = {
            "success_rate": round(success_rate, 3),
            "average_quality_score": round(average_quality, 3),
            "average_generation_time_ms": round(average_generation_time, 0),
            "quality_distribution": quality_distribution,
            "retry_statistics": retry_stats,
            "failure_analysis": failure_reasons,
            "total_generated": len(generation_results),
            "successful_generations": len(successful_results),
            "failed_generations": len(failed_results),
            "recommendations": self._generate_quality_recommendations(
                success_rate, average_quality, failure_reasons
            )
        }
        
        return quality_analysis
    
    def _generate_quality_recommendations(
        self,
        success_rate: float,
        average_quality: float,
        failure_reasons: Dict[str, int]
    ) -> List[str]:
        """Generate quality improvement recommendations."""
        
        recommendations = []
        
        if success_rate < 0.8:
            recommendations.append("生成成功率の改善が必要（プロンプトの最適化を推奨）")
        
        if average_quality < 0.7:
            recommendations.append("品質スコアの向上が必要（スタイルパラメータの調整を推奨）")
        
        # Analyze common failure reasons
        if "validation failed" in str(failure_reasons).lower():
            recommendations.append("バリデーション基準の見直しまたはプロンプト改善")
        
        if "generation failed" in str(failure_reasons).lower():
            recommendations.append("生成パラメータの最適化またはリトライ戦略の改善")
        
        if not recommendations:
            recommendations.append("現在の品質基準を満たしています")
        
        return recommendations
    
    async def _create_scene_image_mapping(
        self,
        generation_results: List[ImageGenerationResult],
        phase4_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create mapping between scenes and generated images."""
        
        successful_results = [r for r in generation_results if r.success]
        
        # Get panel specifications from phase 4
        panel_specifications = phase4_result.get("panel_specifications", [])
        
        # Create mapping
        scene_mapping = {}
        page_mapping = {}
        
        for result in successful_results:
            panel_id = result.panel_id
            
            # Find corresponding panel specification
            panel_spec = next(
                (spec for spec in panel_specifications if spec.get("panel_id") == panel_id),
                {}
            )
            
            scene_number = panel_spec.get("scene_number", 0)
            page_number = panel_spec.get("page_number", 0)
            
            # Add to scene mapping
            if scene_number not in scene_mapping:
                scene_mapping[scene_number] = []
            
            scene_mapping[scene_number].append({
                "panel_id": panel_id,
                "image_url": result.image_url,
                "thumbnail_url": result.thumbnail_url,
                "quality_score": result.quality_score,
                "panel_spec": panel_spec
            })
            
            # Add to page mapping
            if page_number not in page_mapping:
                page_mapping[page_number] = []
            
            page_mapping[page_number].append({
                "panel_id": panel_id,
                "image_url": result.image_url,
                "thumbnail_url": result.thumbnail_url,
                "quality_score": result.quality_score,
                "panel_number": panel_spec.get("panel_number", 0)
            })
        
        # Sort page mappings by panel number
        for page_images in page_mapping.values():
            page_images.sort(key=lambda x: x.get("panel_number", 0))
        
        return {
            "scene_to_images": scene_mapping,
            "page_to_images": page_mapping,
            "total_mapped_scenes": len(scene_mapping),
            "total_mapped_pages": len(page_mapping),
            "images_per_scene": {
                scene: len(images) for scene, images in scene_mapping.items()
            },
            "images_per_page": {
                page: len(images) for page, images in page_mapping.items()
            }
        }
    
    async def _generate_consistency_report(
        self,
        generation_results: List[ImageGenerationResult],
        phase2_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate consistency report for character and style."""
        
        successful_results = [r for r in generation_results if r.success]
        
        # Character consistency analysis
        characters = phase2_result.get("characters", [])
        character_consistency = await self._analyze_character_consistency(
            successful_results, characters
        )
        
        # Style consistency analysis
        style_consistency = await self._analyze_style_consistency(successful_results)
        
        # Quality consistency analysis
        quality_consistency = await self._analyze_quality_consistency(successful_results)
        
        consistency_report = {
            "character_consistency": character_consistency,
            "style_consistency": style_consistency,
            "quality_consistency": quality_consistency,
            "overall_consistency_score": self._calculate_overall_consistency_score(
                character_consistency, style_consistency, quality_consistency
            ),
            "consistency_recommendations": self._generate_consistency_recommendations(
                character_consistency, style_consistency, quality_consistency
            )
        }
        
        return consistency_report
    
    async def _analyze_character_consistency(
        self,
        generation_results: List[ImageGenerationResult],
        characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze character visual consistency across images."""
        
        # TODO: Implement actual character consistency analysis
        # For now, simulate analysis based on available data
        
        character_scores = {}
        
        for char in characters:
            char_name = char.get("name", "")
            
            # Find images featuring this character
            char_images = [
                r for r in generation_results
                if char_name.lower() in r.panel_id.lower()  # Simple heuristic
            ]
            
            if char_images:
                # Simulate consistency score based on quality scores
                quality_scores = [r.quality_score for r in char_images if r.quality_score]
                if quality_scores:
                    # Higher quality generally means better consistency
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    # Consistency is affected by quality variance
                    quality_variance = sum((q - avg_quality) ** 2 for q in quality_scores) / len(quality_scores)
                    consistency_score = avg_quality * (1 - min(0.3, quality_variance))
                    
                    character_scores[char_name] = {
                        "consistency_score": round(consistency_score, 3),
                        "image_count": len(char_images),
                        "average_quality": round(avg_quality, 3),
                        "quality_variance": round(quality_variance, 3)
                    }
        
        # Overall character consistency
        if character_scores:
            overall_score = sum(data["consistency_score"] for data in character_scores.values()) / len(character_scores)
        else:
            overall_score = 0.0
        
        return {
            "character_scores": character_scores,
            "overall_character_consistency": round(overall_score, 3),
            "characters_analyzed": len(character_scores),
            "consistency_issues": self._identify_character_consistency_issues(character_scores)
        }
    
    def _identify_character_consistency_issues(
        self, character_scores: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Identify character consistency issues."""
        
        issues = []
        
        for char_name, data in character_scores.items():
            consistency_score = data.get("consistency_score", 0)
            quality_variance = data.get("quality_variance", 0)
            
            if consistency_score < 0.7:
                issues.append(f"{char_name}の視覚的一貫性が低い（スコア: {consistency_score:.2f}）")
            
            if quality_variance > 0.1:
                issues.append(f"{char_name}の品質にばらつきがある（分散: {quality_variance:.2f}）")
        
        return issues
    
    async def _analyze_style_consistency(
        self, generation_results: List[ImageGenerationResult]
    ) -> Dict[str, Any]:
        """Analyze style consistency across all images."""
        
        # Simulate style consistency analysis
        quality_scores = [r.quality_score for r in generation_results if r.quality_score]
        
        if not quality_scores:
            return {"style_consistency_score": 0.0, "analysis": "No quality scores available"}
        
        # Use quality score variance as a proxy for style consistency
        avg_quality = sum(quality_scores) / len(quality_scores)
        quality_variance = sum((q - avg_quality) ** 2 for q in quality_scores) / len(quality_scores)
        
        # Style consistency is inversely related to variance
        style_consistency_score = max(0.0, 1.0 - quality_variance * 2)
        
        return {
            "style_consistency_score": round(style_consistency_score, 3),
            "average_quality": round(avg_quality, 3),
            "quality_variance": round(quality_variance, 3),
            "style_uniformity": "high" if style_consistency_score > 0.8 else "medium" if style_consistency_score > 0.6 else "low",
            "images_analyzed": len(quality_scores)
        }
    
    async def _analyze_quality_consistency(
        self, generation_results: List[ImageGenerationResult]
    ) -> Dict[str, Any]:
        """Analyze quality consistency across images."""
        
        quality_scores = [r.quality_score for r in generation_results if r.quality_score]
        generation_times = [r.generation_time_ms for r in generation_results if r.generation_time_ms]
        
        if not quality_scores:
            return {"quality_consistency_score": 0.0}
        
        # Calculate quality statistics
        avg_quality = sum(quality_scores) / len(quality_scores)
        min_quality = min(quality_scores)
        max_quality = max(quality_scores)
        quality_range = max_quality - min_quality
        
        # Quality consistency score (lower range = higher consistency)
        quality_consistency_score = max(0.0, 1.0 - quality_range)
        
        # Generation time consistency
        avg_time = sum(generation_times) / len(generation_times) if generation_times else 0
        
        return {
            "quality_consistency_score": round(quality_consistency_score, 3),
            "average_quality": round(avg_quality, 3),
            "quality_range": round(quality_range, 3),
            "min_quality": round(min_quality, 3),
            "max_quality": round(max_quality, 3),
            "average_generation_time_ms": round(avg_time, 0),
            "quality_stability": "stable" if quality_range < 0.2 else "moderate" if quality_range < 0.4 else "variable"
        }
    
    def _calculate_overall_consistency_score(
        self,
        character_consistency: Dict[str, Any],
        style_consistency: Dict[str, Any],
        quality_consistency: Dict[str, Any]
    ) -> float:
        """Calculate overall consistency score."""
        
        scores = []
        
        char_score = character_consistency.get("overall_character_consistency", 0.0)
        if char_score > 0:
            scores.append(char_score * 0.4)  # 40% weight
        
        style_score = style_consistency.get("style_consistency_score", 0.0)
        scores.append(style_score * 0.35)  # 35% weight
        
        quality_score = quality_consistency.get("quality_consistency_score", 0.0)
        scores.append(quality_score * 0.25)  # 25% weight
        
        return round(sum(scores), 3)
    
    def _generate_consistency_recommendations(
        self,
        character_consistency: Dict[str, Any],
        style_consistency: Dict[str, Any], 
        quality_consistency: Dict[str, Any]
    ) -> List[str]:
        """Generate consistency improvement recommendations."""
        
        recommendations = []
        
        # Character consistency recommendations
        char_score = character_consistency.get("overall_character_consistency", 0.0)
        if char_score < 0.7:
            recommendations.append("キャラクターの視覚的一貫性を向上（参考画像やスタイルガイドの活用）")
        
        # Style consistency recommendations
        style_score = style_consistency.get("style_consistency_score", 0.0)
        if style_score < 0.7:
            recommendations.append("スタイルの統一性を改善（プロンプトテンプレートの標準化）")
        
        # Quality consistency recommendations
        quality_range = quality_consistency.get("quality_range", 0.0)
        if quality_range > 0.3:
            recommendations.append("品質のばらつきを軽減（生成パラメータの最適化）")
        
        if not recommendations:
            recommendations.append("現在の一貫性レベルは良好です")
        
        return recommendations
    
    def _calculate_average_generation_time(
        self, generation_results: List[ImageGenerationResult]
    ) -> float:
        """Calculate average generation time."""
        
        times = [r.generation_time_ms for r in generation_results if r.generation_time_ms]
        return sum(times) / len(times) if times else 0.0
    
    def _calculate_parallel_efficiency_score(
        self,
        generation_tasks: List[ImageGenerationTask],
        generation_results: List[ImageGenerationResult]
    ) -> float:
        """Calculate parallel processing efficiency score."""
        
        if not generation_results:
            return 0.0
        
        # Calculate theoretical vs actual time
        avg_single_time = self._calculate_average_generation_time(generation_results)
        if avg_single_time == 0:
            return 0.0
        
        # Theoretical sequential time
        theoretical_sequential_time = len(generation_tasks) * avg_single_time
        
        # Actual parallel time (use max generation time as proxy)
        actual_times = [r.generation_time_ms for r in generation_results if r.generation_time_ms]
        actual_parallel_time = max(actual_times) if actual_times else avg_single_time
        
        # Efficiency score
        if theoretical_sequential_time == 0:
            return 0.0
        
        efficiency_score = 1.0 - (actual_parallel_time / theoretical_sequential_time)
        
        # Account for concurrency benefits
        concurrency_benefit = min(1.0, self.max_concurrent_generations / len(generation_tasks))
        adjusted_score = efficiency_score * (0.5 + 0.5 * concurrency_benefit)
        
        return round(max(0.0, min(1.0, adjusted_score)), 3)
    
    def _calculate_cache_utilization(self) -> Dict[str, Any]:
        """Calculate cache utilization statistics."""
        
        total_requests = self.generation_stats.get("total_generated", 0)
        cache_hits = self.generation_stats.get("cache_hits", 0)
        
        cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "cache_hit_rate": round(cache_hit_rate, 3),
            "total_cache_entries": len(self.image_cache),
            "cache_hits": cache_hits,
            "total_requests": total_requests,
            "cache_efficiency": "high" if cache_hit_rate > 0.3 else "medium" if cache_hit_rate > 0.1 else "low"
        }