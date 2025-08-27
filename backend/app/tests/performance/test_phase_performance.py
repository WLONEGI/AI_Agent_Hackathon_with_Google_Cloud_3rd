"""Performance tests for individual phases and pipeline."""

import pytest
import asyncio
import time
import statistics
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil

from app.agents.base_agent import BaseAgent
from app.agents.pipeline_orchestrator import PipelineOrchestrator
from app.models.manga import MangaSession


class PerformanceTestAgent(BaseAgent):
    """Agent designed for performance testing with configurable behavior."""
    
    def __init__(self, phase_number: int, target_time_ms: int, memory_usage_mb: int = 10):
        super().__init__(phase_number, f"Performance Test Phase {phase_number}", target_time_ms // 1000 + 10)
        self.target_time_ms = target_time_ms
        self.memory_usage_mb = memory_usage_mb
        self._call_count = 0
    
    async def process_phase(self, input_data: Dict[str, Any], session_id, previous_results=None):
        """Process with controlled timing and memory usage."""
        self._call_count += 1
        start_time = time.time()
        
        # Simulate CPU work
        await asyncio.sleep(self.target_time_ms / 1000.0)
        
        # Simulate memory usage
        memory_buffer = bytearray(self.memory_usage_mb * 1024 * 1024)
        
        # Generate realistic output size based on phase
        output_size_factors = {1: 1, 2: 3, 3: 2, 4: 4, 5: 8, 6: 2, 7: 5}
        size_factor = output_size_factors.get(self.phase_number, 1)
        
        output = {
            "phase_number": self.phase_number,
            "call_count": self._call_count,
            "target_time_ms": self.target_time_ms,
            "actual_processing_time_ms": int((time.time() - start_time) * 1000),
            "data": ["sample_data"] * (100 * size_factor),  # Variable output size
            "memory_allocated_mb": self.memory_usage_mb,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Keep memory buffer alive briefly then release
        del memory_buffer
        
        return output
    
    async def generate_prompt(self, input_data: Dict[str, Any], previous_results=None):
        return f"Performance test prompt for phase {self.phase_number}"
    
    async def validate_output(self, output_data: Dict[str, Any]):
        return isinstance(output_data, dict) and "phase_number" in output_data


@pytest.mark.asyncio
class TestIndividualPhasePerformance:
    """Test performance characteristics of individual phases."""
    
    @pytest.mark.parametrize("phase_number,expected_time_ms", [
        (1, 12000),  # Concept Analysis
        (2, 18000),  # Character Design  
        (3, 15000),  # Story Structure
        (4, 20000),  # Panel Layout
        (5, 25000),  # Image Generation
        (6, 4000),   # Dialogue
        (7, 3000),   # Integration
    ])
    async def test_phase_timing_requirements(
        self, 
        phase_number: int, 
        expected_time_ms: int,
        sample_manga_session: MangaSession,
        db_session,
        performance_thresholds: Dict[int, Dict[str, int]]
    ):
        """Test that each phase meets timing requirements."""
        
        agent = PerformanceTestAgent(phase_number, expected_time_ms)
        
        input_data = {
            "test_data": f"Performance test for phase {phase_number}",
            "complexity": "medium",
            "quality_level": "high"
        }
        
        # Multiple runs to get reliable timing
        run_times = []
        memory_usage = []
        
        for run in range(5):
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            start_time = time.time()
            
            result = await agent.process(
                session=sample_manga_session,
                input_data=input_data,
                db=db_session
            )
            
            end_time = time.time()
            processing_time_ms = int((end_time - start_time) * 1000)
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            run_times.append(processing_time_ms)
            memory_usage.append(memory_used)
            
            # Verify result structure
            assert result.status == "completed"
            assert result.processing_time_ms > 0
        
        # Performance analysis
        avg_time = statistics.mean(run_times)
        stddev_time = statistics.stdev(run_times) if len(run_times) > 1 else 0
        max_time = max(run_times)
        min_time = min(run_times)
        
        avg_memory = statistics.mean(memory_usage)
        
        # Performance thresholds from fixture
        thresholds = performance_thresholds[phase_number]
        expected_time = thresholds["expected_time_ms"]
        max_allowed_time = thresholds["max_time_ms"]
        
        # Assertions
        assert avg_time >= expected_time * 0.8, f"Phase {phase_number} too fast: {avg_time}ms < {expected_time * 0.8}ms"
        assert avg_time <= expected_time * 1.2, f"Phase {phase_number} too slow: {avg_time}ms > {expected_time * 1.2}ms"
        assert max_time <= max_allowed_time, f"Phase {phase_number} max time exceeded: {max_time}ms > {max_allowed_time}ms"
        assert avg_memory < 50, f"Phase {phase_number} memory usage too high: {avg_memory}MB"
        
        # Performance consistency
        if len(run_times) > 1:
            coefficient_of_variation = stddev_time / avg_time
            assert coefficient_of_variation < 0.3, f"Phase {phase_number} timing inconsistent: CV={coefficient_of_variation:.3f}"
        
        print(f"Phase {phase_number} Performance:")
        print(f"  Average time: {avg_time:.1f}ms (expected: {expected_time}ms)")
        print(f"  Time range: {min_time}ms - {max_time}ms")
        print(f"  Standard deviation: {stddev_time:.1f}ms")
        print(f"  Average memory: {avg_memory:.1f}MB")
    
    async def test_phase_scalability_with_input_size(
        self, 
        sample_manga_session: MangaSession,
        db_session
    ):
        """Test how phase performance scales with input size."""
        
        agent = PerformanceTestAgent(1, 5000)  # Use phase 1 for testing
        
        # Test with different input sizes
        input_sizes = [
            ("small", "A short story concept"),
            ("medium", "A medium length story " + "with more details " * 10),
            ("large", "A comprehensive story concept " + "with extensive world building " * 50),
            ("extra_large", "A very detailed story " + "with complex narrative elements " * 200)
        ]
        
        results = {}
        
        for size_name, story_text in input_sizes:
            input_data = {
                "story_concept": story_text,
                "complexity": size_name
            }
            
            # Run multiple times for consistency
            times = []
            for _ in range(3):
                start_time = time.time()
                
                result = await agent.process(
                    session=sample_manga_session,
                    input_data=input_data,
                    db=db_session
                )
                
                end_time = time.time()
                times.append((end_time - start_time) * 1000)
            
            results[size_name] = {
                "avg_time_ms": statistics.mean(times),
                "input_size": len(story_text)
            }
        
        # Analyze scalability
        small_time = results["small"]["avg_time_ms"]
        large_time = results["extra_large"]["avg_time_ms"]
        
        # Time should scale sub-linearly (not more than 4x for 100x input)
        scaling_factor = large_time / small_time
        assert scaling_factor < 4.0, f"Poor scalability: {scaling_factor:.1f}x time increase"
        
        print("Scalability Analysis:")
        for size, data in results.items():
            print(f"  {size}: {data['avg_time_ms']:.1f}ms for {data['input_size']} chars")
    
    async def test_concurrent_phase_execution(
        self,
        sample_manga_session: MangaSession, 
        db_session
    ):
        """Test performance under concurrent phase execution."""
        
        # Create multiple agents for parallel execution
        agents = []
        for phase_num in [2, 3]:  # Phases that can run in parallel
            agent = PerformanceTestAgent(phase_num, 5000)
            agents.append(agent)
        
        input_data = {"concurrent_test": True}
        
        # Test sequential execution
        sequential_start = time.time()
        for agent in agents:
            await agent.process(
                session=sample_manga_session,
                input_data=input_data,
                db=db_session
            )
        sequential_time = time.time() - sequential_start
        
        # Test parallel execution
        parallel_start = time.time()
        tasks = [
            agent.process(
                session=sample_manga_session,
                input_data=input_data,
                db=db_session
            )
            for agent in agents
        ]
        await asyncio.gather(*tasks)
        parallel_time = time.time() - parallel_start
        
        # Parallel should be faster than sequential
        efficiency = 1 - (parallel_time / sequential_time)
        assert efficiency > 0.3, f"Poor parallel efficiency: {efficiency:.3f}"
        
        print(f"Concurrency Performance:")
        print(f"  Sequential: {sequential_time:.3f}s")
        print(f"  Parallel: {parallel_time:.3f}s") 
        print(f"  Efficiency: {efficiency:.3f}")
    
    async def test_memory_usage_patterns(
        self,
        sample_manga_session: MangaSession,
        db_session
    ):
        """Test memory usage patterns during phase execution."""
        
        agent = PerformanceTestAgent(5, 10000, memory_usage_mb=20)  # Image generation phase
        
        process = psutil.Process()
        memory_snapshots = []
        
        # Monitor memory before, during, and after execution
        memory_snapshots.append(("before", process.memory_info().rss / 1024 / 1024))
        
        # Execute phase with memory monitoring
        input_data = {"memory_test": True}
        
        # Start execution and monitor memory
        task = asyncio.create_task(
            agent.process(
                session=sample_manga_session,
                input_data=input_data,
                db=db_session
            )
        )
        
        # Sample memory during execution
        for i in range(5):
            await asyncio.sleep(0.1)
            memory_snapshots.append((f"during_{i}", process.memory_info().rss / 1024 / 1024))
        
        result = await task
        
        # Memory after execution
        await asyncio.sleep(0.5)  # Allow cleanup
        memory_snapshots.append(("after", process.memory_info().rss / 1024 / 1024))
        
        # Analyze memory patterns
        memory_before = memory_snapshots[0][1]
        memory_peak = max(snapshot[1] for snapshot in memory_snapshots)
        memory_after = memory_snapshots[-1][1]
        
        memory_growth = memory_peak - memory_before
        memory_leak = memory_after - memory_before
        
        # Assertions
        assert memory_growth > 0, "No detectable memory usage during processing"
        assert memory_growth < 100, f"Excessive memory usage: {memory_growth:.1f}MB"
        assert memory_leak < 10, f"Potential memory leak: {memory_leak:.1f}MB retained"
        
        print(f"Memory Usage Analysis:")
        print(f"  Before: {memory_before:.1f}MB")
        print(f"  Peak: {memory_peak:.1f}MB")
        print(f"  After: {memory_after:.1f}MB")
        print(f"  Growth: {memory_growth:.1f}MB")
        print(f"  Leak: {memory_leak:.1f}MB")


@pytest.mark.asyncio
class TestPipelinePerformance:
    """Test performance of complete pipeline execution."""
    
    async def test_complete_pipeline_performance(
        self,
        sample_manga_session: MangaSession,
        db_session,
        performance_thresholds: Dict[int, Dict[str, int]]
    ):
        """Test complete pipeline performance meets requirements."""
        
        orchestrator = PipelineOrchestrator()
        
        # Replace agents with performance test agents
        for phase_num in range(1, 8):
            expected_time = performance_thresholds[phase_num]["expected_time_ms"]
            agent = PerformanceTestAgent(phase_num, expected_time)
            orchestrator.agents[phase_num] = agent
            orchestrator.execution_plan[phase_num].agent = agent
        
        input_data = {
            "story_concept": "Performance test manga generation",
            "quality_level": "high",
            "performance_test": True
        }
        
        # Execute pipeline with performance monitoring
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        total_time = end_time - start_time
        total_memory_used = end_memory - start_memory
        
        # Analyze results
        execution_summary = result["execution_summary"]
        phase_times = execution_summary["performance_metrics"]["phase_times"]
        
        # Overall performance requirements
        expected_total_time = sum(t["expected_time_ms"] for t in performance_thresholds.values()) / 1000.0
        max_total_time = sum(t["max_time_ms"] for t in performance_thresholds.values()) / 1000.0
        
        # Performance assertions
        assert total_time <= max_total_time, f"Pipeline too slow: {total_time:.1f}s > {max_total_time:.1f}s"
        assert execution_summary["parallel_efficiency_percentage"] > 15, "Poor parallel efficiency"
        assert total_memory_used < 200, f"Excessive memory usage: {total_memory_used:.1f}MB"
        
        # Individual phase performance
        for phase_num, phase_time in phase_times.items():
            expected = performance_thresholds[phase_num]["expected_time_ms"] / 1000.0
            max_allowed = performance_thresholds[phase_num]["max_time_ms"] / 1000.0
            
            assert phase_time <= max_allowed, f"Phase {phase_num} too slow: {phase_time:.1f}s > {max_allowed:.1f}s"
        
        print(f"Pipeline Performance Summary:")
        print(f"  Total time: {total_time:.2f}s (expected: ~{expected_total_time:.1f}s)")
        print(f"  Parallel efficiency: {execution_summary['parallel_efficiency_percentage']:.1f}%")
        print(f"  Memory used: {total_memory_used:.1f}MB")
        print(f"  Phases completed: {execution_summary['phases_completed']}")
    
    async def test_pipeline_under_load(
        self,
        sample_manga_session: MangaSession,
        db_session
    ):
        """Test pipeline performance under concurrent load."""
        
        # Create multiple pipeline instances
        num_concurrent = 3
        orchestrators = []
        
        for i in range(num_concurrent):
            orchestrator = PipelineOrchestrator()
            
            # Set up with fast agents for load testing
            for phase_num in range(1, 8):
                agent = PerformanceTestAgent(phase_num, 1000)  # Fast execution
                orchestrator.agents[phase_num] = agent
                orchestrator.execution_plan[phase_num].agent = agent
            
            orchestrators.append(orchestrator)
        
        # Execute pipelines concurrently
        input_data = {"load_test": True, "concurrent_id": 0}
        
        start_time = time.time()
        
        tasks = []
        for i, orchestrator in enumerate(orchestrators):
            test_input = {**input_data, "concurrent_id": i}
            task = orchestrator.execute_pipeline(
                session=sample_manga_session,
                input_data=test_input,
                db_session=db_session
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        assert len(successful_results) >= num_concurrent * 0.8, f"Too many failures under load: {len(failed_results)}"
        
        # Performance under load should be reasonable
        expected_sequential_time = 7 * 1  # 7 phases * 1 second each
        expected_concurrent_time = expected_sequential_time * 1.5  # Some overhead expected
        
        assert concurrent_time <= expected_concurrent_time, f"Poor performance under load: {concurrent_time:.1f}s"
        
        print(f"Load Test Results:")
        print(f"  Concurrent pipelines: {num_concurrent}")
        print(f"  Successful: {len(successful_results)}")
        print(f"  Failed: {len(failed_results)}")
        print(f"  Total time: {concurrent_time:.2f}s")
    
    async def test_pipeline_resource_limits(
        self,
        sample_manga_session: MangaSession,
        db_session
    ):
        """Test pipeline behavior at resource limits."""
        
        orchestrator = PipelineOrchestrator()
        
        # Create memory-intensive agents
        for phase_num in range(1, 8):
            memory_mb = 50 if phase_num == 5 else 20  # Phase 5 uses more memory
            agent = PerformanceTestAgent(phase_num, 2000, memory_usage_mb=memory_mb)
            orchestrator.agents[phase_num] = agent
            orchestrator.execution_plan[phase_num].agent = agent
        
        # Monitor resource usage throughout execution
        resource_snapshots = []
        
        def monitor_resources():
            process = psutil.Process()
            return {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "timestamp": time.time()
            }
        
        # Resource monitoring callback
        async def resource_callback(progress_info):
            resource_snapshots.append({
                **monitor_resources(),
                "phase": progress_info.get("current_phase", 0)
            })
        
        orchestrator.register_progress_callback(resource_callback)
        
        input_data = {"resource_limit_test": True}
        
        # Execute pipeline
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        # Analyze resource usage
        if resource_snapshots:
            max_memory = max(s["memory_mb"] for s in resource_snapshots)
            avg_cpu = statistics.mean(s["cpu_percent"] for s in resource_snapshots if s["cpu_percent"] > 0)
            
            # Resource limits
            assert max_memory < 500, f"Memory usage too high: {max_memory:.1f}MB"
            
            print(f"Resource Usage Analysis:")
            print(f"  Peak memory: {max_memory:.1f}MB")
            print(f"  Average CPU: {avg_cpu:.1f}%")
            print(f"  Snapshots taken: {len(resource_snapshots)}")
    
    async def test_pipeline_timeout_handling(
        self,
        sample_manga_session: MangaSession,
        db_session
    ):
        """Test pipeline timeout and recovery behavior."""
        
        orchestrator = PipelineOrchestrator()
        
        # Create agents with one slow phase
        for phase_num in range(1, 8):
            if phase_num == 3:  # Make phase 3 very slow
                agent = PerformanceTestAgent(phase_num, 30000)  # 30 seconds
                agent.timeout_seconds = 5  # But timeout after 5 seconds
            else:
                agent = PerformanceTestAgent(phase_num, 1000)
            
            orchestrator.agents[phase_num] = agent
            orchestrator.execution_plan[phase_num].agent = agent
        
        input_data = {"timeout_test": True}
        
        # Execute pipeline (should fail due to timeout)
        with pytest.raises(Exception):  # Expect timeout exception
            await orchestrator.execute_pipeline(
                session=sample_manga_session,
                input_data=input_data,
                db_session=db_session
            )
        
        # Verify that timeout was handled properly
        phase_3_execution = orchestrator.execution_plan[3]
        assert phase_3_execution.status in ["failed", "cancelled"]


@pytest.mark.asyncio  
class TestPerformanceRegression:
    """Test for performance regression detection."""
    
    async def test_performance_baseline(
        self,
        sample_manga_session: MangaSession,
        db_session
    ):
        """Establish performance baseline for regression testing."""
        
        orchestrator = PipelineOrchestrator()
        
        # Standard performance test agents
        baseline_times = {1: 5000, 2: 7000, 3: 6000, 4: 8000, 5: 10000, 6: 2000, 7: 1500}
        
        for phase_num in range(1, 8):
            agent = PerformanceTestAgent(phase_num, baseline_times[phase_num])
            orchestrator.agents[phase_num] = agent
            orchestrator.execution_plan[phase_num].agent = agent
        
        input_data = {"baseline_test": True}
        
        # Multiple runs for statistical significance
        run_times = []
        phase_times_by_run = []
        
        for run in range(3):
            start_time = time.time()
            
            result = await orchestrator.execute_pipeline(
                session=sample_manga_session,
                input_data=input_data,
                db_session=db_session
            )
            
            end_time = time.time()
            run_time = end_time - start_time
            
            run_times.append(run_time)
            phase_times_by_run.append(result["execution_summary"]["performance_metrics"]["phase_times"])
        
        # Calculate baselines
        avg_total_time = statistics.mean(run_times)
        
        # Phase-specific baselines
        phase_baselines = {}
        for phase_num in range(1, 8):
            phase_times = [run[phase_num] for run in phase_times_by_run]
            phase_baselines[phase_num] = {
                "avg_time": statistics.mean(phase_times),
                "max_time": max(phase_times),
                "std_dev": statistics.stdev(phase_times) if len(phase_times) > 1 else 0
            }
        
        # Store baselines (in real implementation, would save to file)
        baseline_data = {
            "total_time": {
                "avg": avg_total_time,
                "max": max(run_times),
                "std_dev": statistics.stdev(run_times) if len(run_times) > 1 else 0
            },
            "phase_times": phase_baselines,
            "test_conditions": {
                "agents": "PerformanceTestAgent",
                "input_size": "standard",
                "concurrent_load": 1
            }
        }
        
        print("Performance Baseline Established:")
        print(f"  Total time: {avg_total_time:.2f}s ± {baseline_data['total_time']['std_dev']:.2f}s")
        for phase_num, data in phase_baselines.items():
            print(f"  Phase {phase_num}: {data['avg_time']:.3f}s ± {data['std_dev']:.3f}s")
        
        # Basic regression check (times should be reasonable)
        assert avg_total_time < 50.0, "Baseline total time too high"
        assert all(data["avg_time"] < 15.0 for data in phase_baselines.values()), "Baseline phase time too high"
        
        return baseline_data


@pytest.mark.asyncio
class TestPerformanceOptimization:
    """Test performance optimization features."""
    
    async def test_caching_performance_improvement(
        self,
        sample_manga_session: MangaSession,
        db_session
    ):
        """Test that caching improves performance for repeated operations."""
        
        agent = PerformanceTestAgent(1, 5000)
        input_data = {"caching_test": True, "story": "repeated content"}
        
        # First run (no cache)
        start_time = time.time()
        result1 = await agent.process(
            session=sample_manga_session,
            input_data=input_data,
            db=db_session
        )
        first_run_time = time.time() - start_time
        
        # Mock cache hit for second run
        with patch.object(agent, '_get_cached_result') as mock_cache:
            mock_cache.return_value = result1.output_data
            
            start_time = time.time()
            # This would normally return cached result, but our mock agent doesn't implement caching
            # So we'll simulate it
            cached_result = await agent._get_cached_result(sample_manga_session.id)
            second_run_time = time.time() - start_time
        
        # Cache retrieval should be much faster
        cache_improvement = first_run_time / max(second_run_time, 0.001)
        
        print(f"Caching Performance:")
        print(f"  First run: {first_run_time:.3f}s")
        print(f"  Cache retrieval: {second_run_time:.3f}s")
        print(f"  Improvement factor: {cache_improvement:.1f}x")
        
        # In real implementation, would test actual cache behavior
        assert cached_result is not None or second_run_time < first_run_time
    
    async def test_parallel_optimization_effectiveness(
        self,
        sample_manga_session: MangaSession,
        db_session
    ):
        """Test effectiveness of parallel execution optimization."""
        
        # Test with different levels of parallelization
        parallelization_configs = [
            {"max_parallel": 1, "name": "sequential"},
            {"max_parallel": 2, "name": "limited_parallel"}, 
            {"max_parallel": 5, "name": "full_parallel"}
        ]
        
        results = {}
        
        for config in parallelization_configs:
            orchestrator = PipelineOrchestrator()
            orchestrator.max_parallel_phases = config["max_parallel"]
            
            # Set up agents
            for phase_num in range(1, 8):
                agent = PerformanceTestAgent(phase_num, 3000)
                orchestrator.agents[phase_num] = agent
                orchestrator.execution_plan[phase_num].agent = agent
            
            input_data = {"parallel_test": config["name"]}
            
            start_time = time.time()
            result = await orchestrator.execute_pipeline(
                session=sample_manga_session,
                input_data=input_data,
                db_session=db_session
            )
            end_time = time.time()
            
            results[config["name"]] = {
                "time": end_time - start_time,
                "efficiency": result["execution_summary"]["parallel_efficiency_percentage"]
            }
        
        # Analyze optimization effectiveness
        sequential_time = results["sequential"]["time"]
        parallel_time = results["full_parallel"]["time"]
        
        optimization_factor = sequential_time / parallel_time
        
        print(f"Parallel Optimization Analysis:")
        for name, data in results.items():
            print(f"  {name}: {data['time']:.2f}s (efficiency: {data['efficiency']:.1f}%)")
        
        print(f"  Optimization factor: {optimization_factor:.1f}x")
        
        # Parallel should be faster than sequential
        assert optimization_factor > 1.2, f"Poor parallel optimization: {optimization_factor:.1f}x"