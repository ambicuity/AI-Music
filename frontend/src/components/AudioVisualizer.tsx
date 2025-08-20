import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

interface AudioVisualizerProps {
  audioData?: {
    frequencyData: number[];
    amplitudeData: number[];
    beatData: any[];
  };
  width?: number;
  height?: number;
  type?: 'spectrum' | 'waveform' | 'circular' | 'bars';
  colorScheme?: string;
  sensitivity?: number;
}

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  audioData,
  width = 800,
  height = 400,
  type = 'spectrum',
  colorScheme = 'default',
  sensitivity = 1.0
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!svgRef.current || !audioData) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Set up dimensions and margins
    const margin = { top: 20, right: 20, bottom: 30, left: 40 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Color schemes
    const colorSchemes = {
      default: d3.scaleSequential(d3.interpolateViridis),
      fire: d3.scaleSequential(d3.interpolateInferno),
      ocean: d3.scaleSequential(d3.interpolateBlues),
      sunset: d3.scaleSequential(d3.interpolateWarm),
      neon: d3.scaleOrdinal(d3.schemeNeon)
    };

    const colorScale = colorSchemes[colorScheme as keyof typeof colorSchemes] || colorSchemes.default;

    switch (type) {
      case 'spectrum':
        renderSpectrum(g, audioData.frequencyData, innerWidth, innerHeight, colorScale, sensitivity);
        break;
      case 'waveform':
        renderWaveform(g, audioData.amplitudeData, innerWidth, innerHeight, colorScale);
        break;
      case 'circular':
        renderCircularSpectrum(g, audioData.frequencyData, innerWidth, innerHeight, colorScale, sensitivity);
        break;
      case 'bars':
        renderBars(g, audioData.frequencyData, innerWidth, innerHeight, colorScale, sensitivity);
        break;
    }

  }, [audioData, width, height, type, colorScheme, sensitivity]);

  const renderSpectrum = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    frequencyData: number[],
    width: number,
    height: number,
    colorScale: any,
    sensitivity: number
  ) => {
    const xScale = d3.scaleLinear()
      .domain([0, frequencyData.length - 1])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(frequencyData) || 255])
      .range([height, 0]);

    const line = d3.line<number>()
      .x((_, i) => xScale(i))
      .y(d => yScale(d * sensitivity))
      .curve(d3.curveBasis);

    // Create gradient
    const gradient = g.append('defs')
      .append('linearGradient')
      .attr('id', 'spectrum-gradient')
      .attr('gradientUnits', 'userSpaceOnUse')
      .attr('x1', 0).attr('y1', height)
      .attr('x2', 0).attr('y2', 0);

    gradient.selectAll('stop')
      .data(colorScale.ticks ? colorScale.ticks(10) : d3.range(10))
      .enter().append('stop')
      .attr('offset', (_, i) => i / 9)
      .attr('stop-color', d => colorScale(d));

    // Draw spectrum area
    const area = d3.area<number>()
      .x((_, i) => xScale(i))
      .y0(height)
      .y1(d => yScale(d * sensitivity))
      .curve(d3.curveBasis);

    g.append('path')
      .datum(frequencyData)
      .attr('class', 'spectrum-area')
      .attr('d', area)
      .style('fill', 'url(#spectrum-gradient)')
      .style('opacity', 0.7);

    // Draw spectrum line
    g.append('path')
      .datum(frequencyData)
      .attr('class', 'spectrum-line')
      .attr('d', line)
      .style('fill', 'none')
      .style('stroke', '#ffffff')
      .style('stroke-width', 2);

    // Add axes
    const xAxis = d3.axisBottom(xScale).ticks(10);
    const yAxis = d3.axisLeft(yScale).ticks(5);

    g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(xAxis)
      .append('text')
      .attr('x', width / 2)
      .attr('y', 25)
      .style('text-anchor', 'middle')
      .style('fill', '#ffffff')
      .text('Frequency');

    g.append('g')
      .call(yAxis)
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -30)
      .attr('x', -height / 2)
      .style('text-anchor', 'middle')
      .style('fill', '#ffffff')
      .text('Amplitude');
  };

  const renderWaveform = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    amplitudeData: number[],
    width: number,
    height: number,
    colorScale: any
  ) => {
    const xScale = d3.scaleLinear()
      .domain([0, amplitudeData.length - 1])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain(d3.extent(amplitudeData) as [number, number])
      .range([height, 0]);

    const line = d3.line<number>()
      .x((_, i) => xScale(i))
      .y(d => yScale(d))
      .curve(d3.curveBasis);

    g.append('path')
      .datum(amplitudeData)
      .attr('class', 'waveform')
      .attr('d', line)
      .style('fill', 'none')
      .style('stroke', colorScale(0.5))
      .style('stroke-width', 2);

    // Add center line
    g.append('line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', height / 2)
      .attr('y2', height / 2)
      .style('stroke', '#444')
      .style('stroke-dasharray', '3,3');
  };

  const renderCircularSpectrum = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    frequencyData: number[],
    width: number,
    height: number,
    colorScale: any,
    sensitivity: number
  ) => {
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 20;

    const angleScale = d3.scaleLinear()
      .domain([0, frequencyData.length - 1])
      .range([0, 2 * Math.PI]);

    const radiusScale = d3.scaleLinear()
      .domain([0, d3.max(frequencyData) || 255])
      .range([50, radius]);

    // Create circular visualization
    g.selectAll('.frequency-bar')
      .data(frequencyData)
      .enter().append('line')
      .attr('class', 'frequency-bar')
      .attr('x1', centerX)
      .attr('y1', centerY)
      .attr('x2', (d, i) => {
        const angle = angleScale(i);
        return centerX + Math.cos(angle - Math.PI / 2) * radiusScale(d * sensitivity);
      })
      .attr('y2', (d, i) => {
        const angle = angleScale(i);
        return centerY + Math.sin(angle - Math.PI / 2) * radiusScale(d * sensitivity);
      })
      .style('stroke', (d, i) => colorScale(i / frequencyData.length))
      .style('stroke-width', 2);

    // Add center circle
    g.append('circle')
      .attr('cx', centerX)
      .attr('cy', centerY)
      .attr('r', 30)
      .style('fill', '#333')
      .style('stroke', '#fff')
      .style('stroke-width', 2);
  };

  const renderBars = (
    g: d3.Selection<SVGGElement, unknown, null, undefined>,
    frequencyData: number[],
    width: number,
    height: number,
    colorScale: any,
    sensitivity: number
  ) => {
    const xScale = d3.scaleBand()
      .domain(frequencyData.map((_, i) => i.toString()))
      .range([0, width])
      .padding(0.1);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(frequencyData) || 255])
      .range([height, 0]);

    g.selectAll('.frequency-bar')
      .data(frequencyData)
      .enter().append('rect')
      .attr('class', 'frequency-bar')
      .attr('x', (_, i) => xScale(i.toString()) || 0)
      .attr('y', d => yScale(d * sensitivity))
      .attr('width', xScale.bandwidth())
      .attr('height', d => height - yScale(d * sensitivity))
      .style('fill', (d, i) => colorScale(i / frequencyData.length))
      .style('opacity', 0.8);
  };

  return (
    <div className="audio-visualizer">
      <div className="visualizer-controls">
        <select 
          value={type} 
          onChange={(e) => {
            // This would need to be handled by parent component
          }}
        >
          <option value="spectrum">Spectrum</option>
          <option value="waveform">Waveform</option>
          <option value="circular">Circular</option>
          <option value="bars">Bars</option>
        </select>
        
        <select
          value={colorScheme}
          onChange={(e) => {
            // This would need to be handled by parent component
          }}
        >
          <option value="default">Default</option>
          <option value="fire">Fire</option>
          <option value="ocean">Ocean</option>
          <option value="sunset">Sunset</option>
          <option value="neon">Neon</option>
        </select>
        
        <input
          type="range"
          min="0.1"
          max="3.0"
          step="0.1"
          value={sensitivity}
          onChange={(e) => {
            // This would need to be handled by parent component
          }}
        />
        <label>Sensitivity: {sensitivity}</label>
      </div>
      
      <svg ref={svgRef} className="visualizer-svg" />
    </div>
  );
};

export default AudioVisualizer;