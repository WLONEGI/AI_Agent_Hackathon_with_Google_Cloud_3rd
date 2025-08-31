import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Home from '@/app/page';

// Mock window.location
delete (window as any).location;
window.location = { href: '/processing' } as any;

describe('Home Page', () => {
  it('renders welcome message', () => {
    render(<Home />);
    expect(screen.getByText('AI漫画生成へようこそ')).toBeInTheDocument();
    expect(screen.getByText('あなたの物語を素敵な漫画に変換します')).toBeInTheDocument();
  });

  it('renders text input area', () => {
    render(<Home />);
    const textarea = screen.getByPlaceholderText('ここに物語のテキストを入力してください...');
    expect(textarea).toBeInTheDocument();
  });

  it('displays character count', async () => {
    const user = userEvent.setup();
    render(<Home />);
    
    const textarea = screen.getByPlaceholderText('ここに物語のテキストを入力してください...');
    const testText = 'This is a test story';
    
    await user.type(textarea, testText);
    
    expect(screen.getByText(`${testText.length} / 5000`)).toBeInTheDocument();
  });

  it('prevents input beyond 5000 characters', async () => {
    const user = userEvent.setup();
    render(<Home />);
    
    const textarea = screen.getByPlaceholderText('ここに物語のテキストを入力してください...') as HTMLTextAreaElement;
    const longText = 'a'.repeat(5001);
    
    await user.clear(textarea);
    await user.type(textarea, longText);
    
    expect(textarea.value.length).toBeLessThanOrEqual(5000);
  });

  it('loads sample stories', () => {
    render(<Home />);
    
    const adventureBtn = screen.getByRole('button', { name: /冒険サンプル/i });
    const romanceBtn = screen.getByRole('button', { name: /恋愛サンプル/i });
    const mysteryBtn = screen.getByRole('button', { name: /ミステリーサンプル/i });
    
    expect(adventureBtn).toBeInTheDocument();
    expect(romanceBtn).toBeInTheDocument();
    expect(mysteryBtn).toBeInTheDocument();
    
    fireEvent.click(adventureBtn);
    const textarea = screen.getByPlaceholderText('ここに物語のテキストを入力してください...') as HTMLTextAreaElement;
    expect(textarea.value).toContain('若き冒険者アレックス');
  });

  it('disables generate button when text is too short', () => {
    render(<Home />);
    
    const generateBtn = screen.getByRole('button', { name: /生成開始/i });
    expect(generateBtn).toBeDisabled();
  });

  it('enables generate button when text is valid', async () => {
    const user = userEvent.setup();
    render(<Home />);
    
    const textarea = screen.getByPlaceholderText('ここに物語のテキストを入力してください...');
    const generateBtn = screen.getByRole('button', { name: /生成開始/i });
    
    await user.type(textarea, 'This is a valid story text');
    
    expect(generateBtn).not.toBeDisabled();
  });

  it('shows alert when text is too short', async () => {
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});
    const user = userEvent.setup();
    render(<Home />);
    
    const textarea = screen.getByPlaceholderText('ここに物語のテキストを入力してください...');
    const generateBtn = screen.getByRole('button', { name: /生成開始/i });
    
    await user.type(textarea, 'Short');
    fireEvent.click(generateBtn);
    
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('物語のテキストが短すぎます。最低10文字以上入力してください。');
    });
    
    alertSpy.mockRestore();
  });

  it('shows loading state when generating', async () => {
    const user = userEvent.setup();
    render(<Home />);
    
    const textarea = screen.getByPlaceholderText('ここに物語のテキストを入力してください...');
    const generateBtn = screen.getByRole('button', { name: /生成開始/i });
    
    await user.type(textarea, 'This is a valid story text for generation');
    fireEvent.click(generateBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/処理中.../i)).toBeInTheDocument();
    });
  });
});