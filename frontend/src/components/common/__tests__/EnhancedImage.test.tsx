import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EnhancedImage, ImagePlaceholder } from '../EnhancedImage';

// Mock Next.js Image component
jest.mock('next/image', () => {
  return function MockImage({ src, alt, onLoad, onError, ...props }: any) {
    return (
      <img
        src={src}
        alt={alt}
        {...props}
        onLoad={onLoad}
        onError={() => onError && onError(new Error('Mock image error'))}
        data-testid="mock-image"
      />
    );
  };
});

describe('EnhancedImage', () => {
  const defaultProps = {
    src: 'https://example.com/image.jpg',
    alt: 'Test image',
    width: 400,
    height: 300,
  };

  it('renders loading state initially', () => {
    render(<EnhancedImage {...defaultProps} />);
    expect(screen.getByText('読み込み中...')).toBeInTheDocument();
  });

  it('renders image when load succeeds', async () => {
    render(<EnhancedImage {...defaultProps} />);

    const image = screen.getByTestId('mock-image');
    fireEvent.load(image);

    await waitFor(() => {
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', defaultProps.src);
    });
  });

  it('shows error state when image fails to load', async () => {
    render(<EnhancedImage {...defaultProps} />);

    const image = screen.getByTestId('mock-image');
    fireEvent.error(image);

    await waitFor(() => {
      expect(screen.getByText('画像の読み込みに失敗しました')).toBeInTheDocument();
      expect(screen.getByText('再試行')).toBeInTheDocument();
    });
  });

  it('tries fallback image when provided', async () => {
    const fallbackSrc = 'https://example.com/fallback.jpg';
    render(
      <EnhancedImage
        {...defaultProps}
        fallbackSrc={fallbackSrc}
      />
    );

    const image = screen.getByTestId('mock-image');
    fireEvent.error(image);

    await waitFor(() => {
      expect(image).toHaveAttribute('src', fallbackSrc);
    });
  });

  it('calls onError callback when image fails', async () => {
    const onError = jest.fn();
    render(
      <EnhancedImage
        {...defaultProps}
        onError={onError}
        retryAttempts={1}
      />
    );

    const image = screen.getByTestId('mock-image');
    fireEvent.error(image);

    await waitFor(() => {
      expect(onError).toHaveBeenCalled();
    });
  });

  it('allows manual retry', async () => {
    render(<EnhancedImage {...defaultProps} retryAttempts={1} />);

    const image = screen.getByTestId('mock-image');
    fireEvent.error(image);

    await waitFor(() => {
      expect(screen.getByText('再試行')).toBeInTheDocument();
    });

    const retryButton = screen.getByText('再試行');
    fireEvent.click(retryButton);

    expect(screen.getByText('読み込み中...')).toBeInTheDocument();
  });
});

describe('ImagePlaceholder', () => {
  it('renders placeholder with default message', () => {
    render(<ImagePlaceholder />);
    expect(screen.getByText('画像が利用できません')).toBeInTheDocument();
  });

  it('renders custom message', () => {
    const customMessage = 'カスタムメッセージ';
    render(<ImagePlaceholder message={customMessage} />);
    expect(screen.getByText(customMessage)).toBeInTheDocument();
  });

  it('applies custom dimensions', () => {
    const { container } = render(
      <ImagePlaceholder width={500} height={400} />
    );

    const placeholder = container.firstChild as HTMLElement;
    expect(placeholder).toHaveStyle({
      width: '500px',
      height: '400px',
    });
  });
});