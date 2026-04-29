import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Typography,
  Tabs,
  Button,
  Space,
  Modal,
  Descriptions,
  List,
  Collapse,
  Badge,
  Empty,
  Alert,
  message
} from 'antd';
import {
  FileTextOutlined,
  WarningOutlined,
  BulbOutlined,
  FolderOpenOutlined,
  DownloadOutlined,
  EyeOutlined,
  CodeOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { cssAnalyzerApi } from '../services/api';
import ForceGraph from './ForceGraph';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const AnalysisResult = ({ 
  analysisData, 
  analysisId, 
  onExportReport, 
  llmConfigured = false 
}) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeModalVisible, setNodeModalVisible] = useState(false);
  const [llmLoading, setLlmLoading] = useState(false);
  const [llmInsights, setLlmInsights] = useState(null);
  const [refactoredCss, setRefactoredCss] = useState(null);

  if (!analysisData) {
    return (
      <Card>
        <Empty
          description="No analysis data yet. Enter a URL above to start analyzing."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const {
    url,
    total_rules,
    total_classes,
    total_selectors,
    css_sources,
    graph_data,
    redundant_items,
    optimization_suggestions,
    statistics
  } = analysisData;

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    setNodeModalVisible(true);
  };

  const handleLLMAnalyze = async () => {
    setLlmLoading(true);
    try {
      const result = await cssAnalyzerApi.llmAnalyze(analysisId);
      setLlmInsights(result.llm_insights);
      message.success('AI analysis completed!');
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      message.error('LLM analysis failed: ' + errorMsg);
      console.error('LLM analysis failed:', error);
    } finally {
      setLlmLoading(false);
    }
  };

  const handleLLMRefactor = async () => {
    setLlmLoading(true);
    try {
      const result = await cssAnalyzerApi.llmRefactor(analysisId);
      setRefactoredCss(result.refactored_css);
      message.success('Refactored CSS generated!');
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      message.error('Refactoring failed: ' + errorMsg);
      console.error('Refactoring failed:', error);
    } finally {
      setLlmLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'blue';
    }
  };

  const redundancyColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => (
        <Tag color={
          type === 'duplicate-selector' ? 'red' :
          type === 'duplicate-color' ? 'blue' : 'orange'
        }>
          {type.replace('-', ' ').toUpperCase()}
        </Tag>
      ),
      width: 150
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value, record) => (
        <Space>
          {record.type === 'duplicate-color' && (
            <span
              className="color-preview"
              style={{ backgroundColor: value }}
            />
          )}
          <code>{value}</code>
        </Space>
      )
    },
    {
      title: 'Occurrences',
      dataIndex: 'locations',
      key: 'occurrences',
      render: (locations) => (
        <Badge count={locations?.length || 0} style={{ backgroundColor: '#faad14' }} />
      ),
      width: 120
    },
    {
      title: 'Suggestion',
      dataIndex: 'suggestion',
      key: 'suggestion',
      ellipsis: true
    }
  ];

  const suggestionColumns = [
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (cat) => <Tag color="blue">{cat.toUpperCase()}</Tag>,
      width: 120
    },
    {
      title: 'Issue',
      dataIndex: 'issue',
      key: 'issue'
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (sev) => (
        <Tag color={getSeverityColor(sev)}>{sev.toUpperCase()}</Tag>
      ),
      width: 100
    },
    {
      title: 'Suggestion',
      dataIndex: 'suggestion',
      key: 'suggestion',
      ellipsis: true
    }
  ];

  const cssSourceColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => (
        <Tag color={
          type === 'external' ? 'blue' :
          type === 'inline' ? 'green' : 'purple'
        }>
          {type.toUpperCase()}
        </Tag>
      ),
      width: 100
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      ellipsis: true,
      render: (source) => <Text code>{source}</Text>
    },
    {
      title: 'Rules',
      dataIndex: 'rules_count',
      key: 'rules_count',
      width: 80
    },
    {
      title: 'Size',
      dataIndex: 'size_bytes',
      key: 'size_bytes',
      render: (size) => size ? `${(size / 1024).toFixed(2)} KB` : '-',
      width: 100
    }
  ];

  const tabItems = [
    {
      key: 'overview',
      label: (
        <Space>
          <FileTextOutlined />
          Overview
        </Space>
      ),
      children: (
        <div>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={12} sm={6}>
              <Card className="stat-card">
                <Statistic
                  title="Total Rules"
                  value={total_rules}
                  valueStyle={{ color: '#667eea' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="stat-card">
                <Statistic
                  title="CSS Classes"
                  value={total_classes}
                  valueStyle={{ color: '#2ed573' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="stat-card">
                <Statistic
                  title="Selectors"
                  value={total_selectors}
                  valueStyle={{ color: '#ff4757' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="stat-card">
                <Statistic
                  title="CSS Sources"
                  value={css_sources?.length || 0}
                  valueStyle={{ color: '#ffa502' }}
                />
              </Card>
            </Col>
          </Row>

          {statistics && (
            <Card title="Detailed Statistics" style={{ marginBottom: 24 }}>
              <Row gutter={[16, 16]}>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Unique Colors"
                    value={statistics.unique_colors || 0}
                    suffix="colors"
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Color Usages"
                    value={statistics.color_usage_count || 0}
                    suffix="times"
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Avg Nesting Depth"
                    value={statistics.average_depth || 0}
                    precision={2}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Max Nesting Depth"
                    value={statistics.max_depth || 0}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Orphan Classes"
                    value={statistics.orphan_classes || 0}
                    valueStyle={{ color: '#ffa502' }}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Leaf Classes"
                    value={statistics.leaf_classes || 0}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Graph Nodes"
                    value={graph_data?.nodes?.length || 0}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Relationships"
                    value={graph_data?.edges?.length || 0}
                  />
                </Col>
              </Row>
            </Card>
          )}

          <Card title="CSS Sources" className="analysis-result-card">
            <Table
              columns={cssSourceColumns}
              dataSource={css_sources}
              rowKey={(record, index) => index}
              pagination={false}
              size="small"
            />
          </Card>
        </div>
      )
    },
    {
      key: 'redundancies',
      label: (
        <Space>
          <WarningOutlined />
          Redundancies
          {redundant_items?.length > 0 && (
            <Badge count={redundant_items.length} style={{ backgroundColor: '#faad14' }} />
          )}
        </Space>
      ),
      children: (
        <div>
          {redundant_items && redundant_items.length > 0 ? (
            <Table
              columns={redundancyColumns}
              dataSource={redundant_items}
              rowKey={(record, index) => index}
              pagination={{ pageSize: 10 }}
              expandable={{
                expandedRowRender: (record) => (
                  <List
                    size="small"
                    header={<Text strong>Locations:</Text>}
                    dataSource={record.locations?.slice(0, 10)}
                    renderItem={(item) => (
                      <List.Item>
                        <Space>
                          <Text code>{item.selector}</Text>
                          <Text type="secondary">@</Text>
                          <Text>{item.source_file || 'unknown'}</Text>
                          {item.line_number && <Text type="secondary">:{item.line_number}</Text>}
                        </Space>
                      </List.Item>
                    )}
                  />
                )
              }}
            />
          ) : (
            <Empty description="No redundant styles found. Great job!" />
          )}
        </div>
      )
    },
    {
      key: 'suggestions',
      label: (
        <Space>
          <BulbOutlined />
          Suggestions
          {optimization_suggestions?.length > 0 && (
            <Badge count={optimization_suggestions.length} style={{ backgroundColor: '#52c41a' }} />
          )}
        </Space>
      ),
      children: (
        <div>
          {optimization_suggestions && optimization_suggestions.length > 0 ? (
            <Table
              columns={suggestionColumns}
              dataSource={optimization_suggestions}
              rowKey={(record, index) => index}
              pagination={{ pageSize: 10 }}
              expandable={{
                expandedRowRender: (record) => (
                  <div>
                    <Text strong>Affected items:</Text>
                    <div style={{ marginTop: 8 }}>
                      <Space wrap>
                        {record.affected_items?.map((item, idx) => (
                          <Tag key={idx}>{item}</Tag>
                        ))}
                      </Space>
                    </div>
                  </div>
                )
              }}
            />
          ) : (
            <Empty description="No optimization suggestions. Your CSS looks good!" />
          )}
        </div>
      )
    }
  ];

  if (llmConfigured) {
    tabItems.push({
      key: 'llm',
      label: (
        <Space>
          <RobotOutlined />
          AI Analysis
        </Space>
      ),
      children: (
        <div>
          <Card
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<RobotOutlined />}
                  loading={llmLoading}
                  onClick={handleLLMAnalyze}
                >
                  Get AI Insights
                </Button>
                <Button
                  icon={<CodeOutlined />}
                  loading={llmLoading}
                  onClick={handleLLMRefactor}
                >
                  Generate Refactored CSS
                </Button>
              </Space>
            }
          >
            <Alert
              message="AI-Powered Analysis"
              description={
                <div>
                  <p>Use your configured LLM to get deeper insights and automatic refactoring suggestions for your CSS.</p>
                  {analysisId && (
                    <p><Text type="secondary">Analysis ID: {analysisId}</Text></p>
                  )}
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />

            {llmInsights && (
              <Card title="AI Insights" style={{ marginBottom: 16 }}>
                <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                  {llmInsights}
                </Paragraph>
              </Card>
            )}

            {refactoredCss && (
              <Card title="Refactored CSS Suggestion">
                <pre className="code-block">{refactoredCss}</pre>
              </Card>
            )}

            {!llmInsights && !refactoredCss && (
              <Empty
                description="Click 'Get AI Insights' or 'Generate Refactored CSS' to use AI analysis"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Card>
        </div>
      )
    });
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <FolderOpenOutlined />
            <span>Analysis Results</span>
            <Text type="secondary" code>{url}</Text>
            {analysisId && (
              <Tag color="blue">ID: {analysisId.substring(0, 8)}...</Tag>
            )}
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={onExportReport}
          >
            Export Report
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        <Tabs defaultActiveKey="overview" items={tabItems} />
      </Card>

      {graph_data && graph_data.nodes && graph_data.nodes.length > 0 && (
        <ForceGraph
          graphData={graph_data}
          onNodeClick={handleNodeClick}
        />
      )}

      <Modal
        title={
          <Space>
            <EyeOutlined />
            <span>Class Details: {selectedNode?.name}</span>
          </Space>
        }
        open={nodeModalVisible}
        onCancel={() => setNodeModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedNode && (
          <div>
            <Descriptions bordered column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Name">{selectedNode.name}</Descriptions.Item>
              <Descriptions.Item label="Type">{selectedNode.type}</Descriptions.Item>
              <Descriptions.Item label="Specificity">{selectedNode.specificity?.toFixed(3)}</Descriptions.Item>
              <Descriptions.Item label="Rules Count">{selectedNode.rules?.length || 0}</Descriptions.Item>
              <Descriptions.Item label="Parent Classes" span={2}>
                {selectedNode.parent_classes?.length > 0 ? (
                  <Space wrap>
                    {selectedNode.parent_classes.map((p, i) => <Tag key={i}>{p}</Tag>)}
                  </Space>
                ) : (
                  <Text type="secondary">None</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Child Classes" span={2}>
                {selectedNode.child_classes?.length > 0 ? (
                  <Space wrap>
                    {selectedNode.child_classes.map((c, i) => <Tag key={i}>{c}</Tag>)}
                  </Space>
                ) : (
                  <Text type="secondary">None</Text>
                )}
              </Descriptions.Item>
            </Descriptions>

            {selectedNode.rules && selectedNode.rules.length > 0 && (
              <Collapse>
                <Panel header={`CSS Rules (${selectedNode.rules.length})`} key="rules">
                  {selectedNode.rules.map((rule, idx) => (
                    <div key={idx} style={{ marginBottom: 16, padding: 12, background: '#fafafa', borderRadius: 4 }}>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong code>{rule.selector}</Text>
                        <Text type="secondary" style={{ marginLeft: 8 }}>
                          (specificity: {rule.specificity?.toFixed(3)})
                        </Text>
                      </div>
                      <pre className="code-block" style={{ margin: 0, fontSize: 12 }}>
                        {`${rule.selector} {
${Object.entries(rule.declarations || {}).map(([k, v]) => `  ${k}: ${v};`).join('\n')}
}`}
                      </pre>
                      {rule.source_file && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          Source: {rule.source_file}
                          {rule.line_number && `:${rule.line_number}`}
                        </Text>
                      )}
                    </div>
                  ))}
                </Panel>
              </Collapse>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AnalysisResult;
