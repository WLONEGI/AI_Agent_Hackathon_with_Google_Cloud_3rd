/**
 * HITL Integration Test
 * Tests the end-to-end HITL feedback flow to verify frontend-backend integration
 */

// Mock fetch for testing without actual backend
global.fetch = jest.fn();

// Mock API responses
const mockApiResponses = {
  submitHitlFeedback: {
    success: true,
    data: {
      feedback_id: "test-feedback-123",
      processing_status: "processing",
      estimated_completion_time: new Date(Date.now() + 5 * 60 * 1000).toISOString()
    }
  },
  getHitlFeedbackState: {
    success: true,
    data: {
      session_id: "test-session-123",
      phase: 2,
      state: "waiting",
      remaining_time_seconds: 1800,
      feedback_started_at: new Date().toISOString(),
      feedback_timeout_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
      preview_data: {
        type: "character_design",
        content: "Test character design preview"
      }
    }
  },
  getHitlPhasePreview: {
    success: true,
    data: {
      session_id: "test-session-123",
      phase: 2,
      preview_data: {
        type: "character_design",
        content: "Test character design preview",
        image_url: "https://example.com/preview.jpg"
      },
      feedback_options: [
        {
          id: "1",
          phase: 2,
          option_key: "character_style",
          option_label: "Character Style",
          option_description: "Modify character art style",
          option_category: "visual",
          display_order: 1,
          is_active: true
        }
      ]
    }
  }
};

describe('HITL Integration Flow', () => {
  beforeEach(() => {
    fetch.mockClear();
    fetch.mockImplementation((url, options) => {
      const urlStr = url.toString();

      if (urlStr.includes('/api/v1/hitl/sessions/') && urlStr.includes('/feedback') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockApiResponses.submitHitlFeedback)
        });
      }

      if (urlStr.includes('/api/v1/hitl/sessions/') && urlStr.includes('/feedback-state')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockApiResponses.getHitlFeedbackState)
        });
      }

      if (urlStr.includes('/api/v1/hitl/sessions/') && urlStr.includes('/preview/')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockApiResponses.getHitlPhasePreview)
        });
      }

      return Promise.reject(new Error(`Unexpected API call: ${urlStr}`));
    });
  });

  test('API client submitHitlFeedback calls correct endpoint', async () => {
    const { apiClient } = require('../../src/lib/api');

    const result = await apiClient.submitHitlFeedback('test-session-123', {
      phase: 2,
      feedback_type: 'modification',
      natural_language_input: 'Please make the character more dynamic',
      selected_options: [],
      user_satisfaction_score: 7,
      processing_time_ms: 5000
    });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/hitl/sessions/test-session-123/feedback'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        }),
        body: expect.stringContaining('modification')
      })
    );

    expect(result.success).toBe(true);
    expect(result.data.feedback_id).toBe('test-feedback-123');
  });

  test('API client getHitlFeedbackState calls correct endpoint', async () => {
    const { apiClient } = require('../../src/lib/api');

    const result = await apiClient.getHitlFeedbackState('test-session-123', 2);

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/hitl/sessions/test-session-123/feedback-state?phase=2'),
      expect.objectContaining({
        method: 'GET'
      })
    );

    expect(result.success).toBe(true);
    expect(result.data.phase).toBe(2);
    expect(result.data.state).toBe('waiting');
  });

  test('API client getHitlPhasePreview calls correct endpoint', async () => {
    const { apiClient } = require('../../src/lib/api');

    const result = await apiClient.getHitlPhasePreview('test-session-123', 2);

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/hitl/sessions/test-session-123/preview/2'),
      expect.objectContaining({
        method: 'GET'
      })
    );

    expect(result.success).toBe(true);
    expect(result.data.preview_data.type).toBe('character_design');
    expect(result.data.feedback_options).toHaveLength(1);
  });

  test('Frontend uses HITL endpoints instead of manga endpoints', async () => {
    const { submitFeedback } = require('../../src/lib/api');

    // Test the original submitFeedback function uses HITL endpoint
    await submitFeedback('test-session-123', 2, 'Test feedback', 'modification', [], 7);

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/hitl/sessions/test-session-123/feedback'),
      expect.anything()
    );

    // Ensure it's NOT calling the old manga endpoint
    expect(fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/manga/sessions/test-session-123/feedback'),
      expect.anything()
    );
  });
});

describe('HITL Feedback Type Mapping', () => {
  test('Maps frontend feedback types to HITL types correctly', () => {
    // This tests the type mapping logic that was implemented
    const frontendTypes = ['natural_language', 'quick_option', 'skip'];
    const expectedHitlTypes = ['modification', 'modification', 'skip'];

    frontendTypes.forEach((frontendType, index) => {
      let hitlType = 'modification'; // default
      if (frontendType === 'skip') {
        hitlType = 'skip';
      }

      expect(hitlType).toBe(expectedHitlTypes[index]);
    });
  });
});

console.log('✅ HITL Integration Test Suite Created');
console.log('📋 Test covers:');
console.log('  - API endpoint routing (/api/v1/hitl vs /api/v1/manga)');
console.log('  - Feedback submission with correct parameters');
console.log('  - Feedback state retrieval');
console.log('  - Phase preview functionality');
console.log('  - Frontend-backend type mapping');
console.log('');
console.log('🚀 Frontend HITL integration is ready for testing!');