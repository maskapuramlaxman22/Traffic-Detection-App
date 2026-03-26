import React, { useMemo } from 'react';

/**
 * RouteVisualization Component
 * 
 * Displays route with intermediate stops in format:
 * Source → ○ → ○ → ○ → Destination
 * 
 * Each circle shows traffic indicator (🟢 🟡 🔴) above it
 * Distance and time displayed below
 */
const RouteVisualization = ({ 
  source, 
  destination, 
  routeData, 
  onViewMap 
}) => {
  
  // Generate intermediate waypoints from route data
  const waypoints = useMemo(() => {
    if (!routeData || !routeData.steps) return [];
    
    // Calculate waypoints based on route steps
    // Show significant points along the route
    const steps = routeData.steps || [];
    
    if (steps.length === 0) {
      // If no steps, create synthetic waypoints based on route length
      const numWaypoints = Math.max(2, Math.min(4, Math.ceil(routeData.distance_km / 5)));
      return Array.from({ length: numWaypoints }).map((_, idx) => ({
        id: idx,
        name: `Via Point ${idx + 1}`,
        traffic_level: 'Moderate', // Default to moderate
        distance_from_start: (routeData.distance_km / (numWaypoints + 1)) * (idx + 1),
        congestion_percentage: Math.random() * 100
      }));
    }
    
    // Use actual steps from routing service
    return steps.slice(0, Math.min(4, steps.length)).map((step, idx) => ({
      id: idx,
      name: step.name || `Via Point ${idx + 1}`,
      traffic_level: predictTrafficLevel(step),
      distance_from_start: step.distance_meters / 1000,
      congestion_percentage: (Math.random() * 100)
    }));
  }, [routeData]);

  // Predict traffic level based on distance and time
  const predictTrafficLevel = (step) => {
    if (!step) return 'Light';
    
    // If actual speed is available, use it
    const distance = step.distance_meters || 0;
    const duration = step.duration_seconds || 0;
    
    if (distance > 0 && duration > 0) {
      const speed = (distance / 1000) / (duration / 3600); // km/h
      
      // Speed thresholds (typical India urban traffic)
      if (speed > 40) return 'Light';
      if (speed > 20) return 'Moderate';
      return 'Heavy';
    }
    
    return 'Moderate';
  };

  // Get traffic color and emoji
  const getTrafficIndicator = (level) => {
    switch(level) {
      case 'Light':
        return { emoji: '🟢', color: '#4caf50', bgColor: '#e8f5e9', label: 'Light' };
      case 'Moderate':
        return { emoji: '🟡', color: '#ff9800', bgColor: '#fff3e0', label: 'Moderate' };
      case 'Heavy':
        return { emoji: '🔴', color: '#f44336', bgColor: '#ffebee', label: 'Heavy' };
      default:
        return { emoji: '⚪', color: '#9e9e9e', bgColor: '#f5f5f5', label: 'Unknown' };
    }
  };

  // Generate Google Maps URL
  const generateMapURL = (mapService = 'google') => {
    const sourceName = source?.name || source?.address || source;
    const destName = destination?.name || destination?.address || destination;
    
    if (mapService === 'google') {
      return `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(sourceName)}&destination=${encodeURIComponent(destName)}`;
    } else {
      // OpenStreetMap
      const sourceCoords = source?.latitude && source?.longitude 
        ? `${source.latitude},${source.longitude}` 
        : sourceName;
      const destCoords = destination?.latitude && destination?.longitude 
        ? `${destination.latitude},${destination.longitude}` 
        : destName;
      
      return `https://www.openstreetmap.org/directions?route=${encodeURIComponent(sourceCoords)};${encodeURIComponent(destCoords)}`;
    }
  };

  return (
    <div style={{
      marginTop: '25px',
      padding: '20px',
      background: '#f8f9fa',
      borderRadius: '8px',
      border: '2px solid #e0e0e0'
    }}>
      {/* Route Visualization */}
      <div style={{
        marginBottom: '25px',
        padding: '20px',
        background: '#fff',
        borderRadius: '6px',
        border: '1px solid #ddd'
      }}>
        {/* Header */}
        <div style={{ marginBottom: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#333', fontSize: '1.1em' }}>
            📍 Route Visualization
          </h4>
          <p style={{ margin: '0', color: '#666', fontSize: '0.9em' }}>
            {waypoints.length} intermediate stops
          </p>
        </div>

        {/* Route Flow Diagram */}
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '8px',
          overflowX: 'auto',
          paddingBottom: '20px'
        }}>
          {/* SOURCE */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '80px' }}>
            <div style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              background: '#2196F3',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 'bold',
              fontSize: '1.3em',
              marginBottom: '8px',
              boxShadow: '0 2px 8px rgba(33,150,243,0.3)'
            }}>
              📍
            </div>
            <div style={{
              fontSize: '0.85em',
              fontWeight: '600',
              color: '#333',
              textAlign: 'center',
              wordBreak: 'break-word',
              maxWidth: '80px'
            }}>
              {source?.name || 'Start'}
            </div>
          </div>

          {/* ARROW AND INTERMEDIATE POINTS */}
          {waypoints.map((waypoint, idx) => (
            <React.Fragment key={waypoint.id}>
              {/* Arrow */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                flex: '0 0 auto',
                marginTop: '30px'
              }}>
                <div style={{
                  fontSize: '1.5em',
                  color: '#999',
                  userSelect: 'none'
                }}>→</div>
              </div>

              {/* Waypoint Circle with Traffic Indicator */}
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                minWidth: '80px'
              }}>
                {/* Traffic Indicator Above */}
                <div style={{
                  marginBottom: '8px',
                  textAlign: 'center'
                }}>
                  <div style={{
                    fontSize: '1.8em',
                    marginBottom: '4px'
                  }}>
                    {getTrafficIndicator(waypoint.traffic_level).emoji}
                  </div>
                  <div style={{
                    fontSize: '0.75em',
                    color: getTrafficIndicator(waypoint.traffic_level).color,
                    fontWeight: '600'
                  }}>
                    {getTrafficIndicator(waypoint.traffic_level).label}
                  </div>
                </div>

                {/* Circle Node */}
                <div style={{
                  width: '50px',
                  height: '50px',
                  borderRadius: '50%',
                  background: getTrafficIndicator(waypoint.traffic_level).bgColor,
                  border: `3px solid ${getTrafficIndicator(waypoint.traffic_level).color}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: getTrafficIndicator(waypoint.traffic_level).color,
                  fontWeight: 'bold',
                  marginBottom: '8px',
                  fontSize: '1.1em'
                }}>
                  {idx + 1}
                </div>

                {/* Waypoint Name */}
                <div style={{
                  fontSize: '0.8em',
                  color: '#555',
                  textAlign: 'center',
                  wordBreak: 'break-word',
                  maxWidth: '80px',
                  fontWeight: '500'
                }}>
                  {waypoint.name}
                </div>
              </div>
            </React.Fragment>
          ))}

          {/* Arrow to Destination */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            flex: '0 0 auto',
            marginTop: '30px'
          }}>
            <div style={{
              fontSize: '1.5em',
              color: '#999',
              userSelect: 'none'
            }}>→</div>
          </div>

          {/* DESTINATION */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '80px' }}>
            {/* Traffic Indicator for Destination */}
            <div style={{
              marginBottom: '8px',
              textAlign: 'center',
              height: '30px'
            }}>
              <div style={{
                fontSize: '1.4em',
                marginBottom: '4px'
              }}>
                {getTrafficIndicator(routeData?.destination_traffic_level || 'Light').emoji}
              </div>
            </div>

            <div style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              background: '#4caf50',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 'bold',
              fontSize: '1.3em',
              marginBottom: '8px',
              boxShadow: '0 2px 8px rgba(76,175,80,0.3)'
            }}>
              🎯
            </div>
            <div style={{
              fontSize: '0.85em',
              fontWeight: '600',
              color: '#333',
              textAlign: 'center',
              wordBreak: 'break-word',
              maxWidth: '80px'
            }}>
              {destination?.name || 'End'}
            </div>
          </div>
        </div>
      </div>

      {/* Route Details Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: '15px',
        marginBottom: '20px'
      }}>
        {/* Distance */}
        <div style={{
          padding: '15px',
          background: '#fff',
          borderRadius: '6px',
          border: '1px solid #ddd',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '0.9em',
            color: '#666',
            marginBottom: '8px',
            fontWeight: '500'
          }}>
            📏 Distance
          </div>
          <div style={{
            fontSize: '1.5em',
            fontWeight: 'bold',
            color: '#2196F3'
          }}>
            {routeData?.distance_km ? `${routeData.distance_km.toFixed(1)} km` : 'N/A'}
          </div>
        </div>

        {/* Time */}
        <div style={{
          padding: '15px',
          background: '#fff',
          borderRadius: '6px',
          border: '1px solid #ddd',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '0.9em',
            color: '#666',
            marginBottom: '8px',
            fontWeight: '500'
          }}>
            ⏱️ Estimated Time
          </div>
          <div style={{
            fontSize: '1.5em',
            fontWeight: 'bold',
            color: '#ff9800'
          }}>
            {routeData?.duration_minutes ? `${Math.ceil(routeData.duration_minutes)} min` : 'N/A'}
          </div>
        </div>

        {/* Overall Traffic */}
        <div style={{
          padding: '15px',
          background: '#fff',
          borderRadius: '6px',
          border: '1px solid #ddd',
          textAlign: 'center'
        }}>
          <div style={{
            fontSize: '0.9em',
            color: '#666',
            marginBottom: '8px',
            fontWeight: '500'
          }}>
            🚦 Overall Traffic
          </div>
          <div style={{
            fontSize: '1.1em',
            fontWeight: 'bold',
            padding: '6px 12px',
            borderRadius: '4px',
            background: routeData?.traffic_level === 'Heavy' 
              ? '#ffebee' 
              : routeData?.traffic_level === 'Moderate' 
              ? '#fff3e0' 
              : '#e8f5e9',
            color: routeData?.traffic_level === 'Heavy' 
              ? '#f44336' 
              : routeData?.traffic_level === 'Moderate' 
              ? '#ff9800' 
              : '#4caf50'
          }}>
            {getTrafficIndicator(routeData?.traffic_level).emoji} {routeData?.traffic_level || 'Unknown'}
          </div>
        </div>
      </div>

      {/* View on Map Button */}
      <div style={{
        display: 'flex',
        gap: '12px',
        justifyContent: 'center'
      }}>
        <button
          onClick={() => window.open(generateMapURL('google'), '_blank')}
          style={{
            padding: '12px 24px',
            background: '#2196F3',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '1em',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
          onMouseOver={(e) => {
            e.target.style.background = '#1976D2';
            e.target.style.transform = 'translateY(-2px)';
            e.target.style.boxShadow = '0 4px 12px rgba(33,150,243,0.4)';
          }}
          onMouseOut={(e) => {
            e.target.style.background = '#2196F3';
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = 'none';
          }}
        >
          🗺️ View on Google Maps
        </button>

        <button
          onClick={() => window.open(generateMapURL('osm'), '_blank')}
          style={{
            padding: '12px 24px',
            background: '#4caf50',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '1em',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
          onMouseOver={(e) => {
            e.target.style.background = '#388e3c';
            e.target.style.transform = 'translateY(-2px)';
            e.target.style.boxShadow = '0 4px 12px rgba(76,175,80,0.4)';
          }}
          onMouseOut={(e) => {
            e.target.style.background = '#4caf50';
            e.target.style.transform = 'translateY(0)';
            e.target.style.boxShadow = 'none';
          }}
        >
          🗺️ View on OSM
        </button>
      </div>

      {/* Info Message */}
      <div style={{
        marginTop: '15px',
        padding: '12px',
        background: '#e3f2fd',
        border: '1px solid #90caf9',
        borderRadius: '4px',
        fontSize: '0.9em',
        color: '#1565c0',
        textAlign: 'center'
      }}>
        💡 Click "View on Map" to see the detailed route with turn-by-turn directions
      </div>
    </div>
  );
};

export default RouteVisualization;
