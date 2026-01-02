<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Hero Section -->
    <div class="bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 text-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        
        <div class="text-center">
          <h1 class="text-4xl md:text-6xl font-bold mb-6">
            TPRM Risk Intelligence
          </h1>
          <p class="text-xl md:text-2xl mb-8 text-blue-100">
            Comprehensive Third Party Risk Management Platform
          </p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" class="bg-white text-blue-900 hover:bg-gray-100">
              <Shield class="h-5 w-5 mr-2" />
              Risk Dashboard
            </Button>
            <Button size="lg" variant="outline" class="border-white text-white hover:bg-white hover:text-blue-900">
              <BarChart3 class="h-5 w-5 mr-2" />
              View Analytics
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Risk Overview Cards -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card class="bg-white shadow-lg border-l-4 border-l-red-500">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium text-gray-600">Critical Risks</CardTitle>
            <AlertTriangle class="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-red-600">23</div>
            <p class="text-xs text-muted-foreground">
              <span class="text-red-600 font-medium">+3</span> from last week
            </p>
          </CardContent>
        </Card>

        <Card class="bg-white shadow-lg border-l-4 border-l-orange-500">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium text-gray-600">High Priority</CardTitle>
            <TrendingUp class="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-orange-600">47</div>
            <p class="text-xs text-muted-foreground">
              <span class="text-orange-600 font-medium">+8</span> from last week
            </p>
          </CardContent>
        </Card>

        <Card class="bg-white shadow-lg border-l-4 border-l-blue-500">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium text-gray-600">Active Vendors</CardTitle>
            <Building2 class="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-blue-600">1,247</div>
            <p class="text-xs text-muted-foreground">
              <span class="text-green-600 font-medium">+12</span> new this month
            </p>
          </CardContent>
        </Card>

        <Card class="bg-white shadow-lg border-l-4 border-l-green-500">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle class="text-sm font-medium text-gray-600">Risk Score</CardTitle>
            <Target class="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold text-green-600">7.2</div>
            <p class="text-xs text-muted-foreground">
              <span class="text-green-600 font-medium">+0.3</span> improvement
            </p>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <!-- Risk Analytics Section -->
      <div class="mb-12">
        <div class="flex items-center justify-between mb-8">
          <div>
            <h2 class="text-3xl font-bold text-gray-900">Risk Analytics Dashboard</h2>
            <p class="text-sm text-gray-500 mt-1">Current tab: {{ activeAnalyticsTab }} | Data loaded: {{ riskDistributionData.length }} items</p>
          </div>
          <div class="flex gap-2">
            <Button variant="outline" size="sm">
              <Download class="h-4 w-4 mr-2" />
              Export Report
            </Button>
            <Button variant="outline" size="sm">
              <RefreshCw class="h-4 w-4 mr-2" />
              Refresh Data
            </Button>
          </div>
        </div>

         <!-- Analytics Tabs -->
         <Tabs class="w-full">
           <TabsList class="grid w-full grid-cols-2 h-10">
             <TabsTrigger 
               value="overview" 
               :active="activeAnalyticsTab === 'overview'"
               @click="activeAnalyticsTab = 'overview'"
               class="flex items-center justify-center"
             >
               Overview
             </TabsTrigger>
             <TabsTrigger 
               value="heatmap" 
               :active="activeAnalyticsTab === 'heatmap'"
               @click="activeAnalyticsTab = 'heatmap'"
               class="flex items-center justify-center"
             >
               Heatmap
             </TabsTrigger>
           </TabsList>

          <!-- Overview Tab -->
          <TabsContent value="overview" :active="activeAnalyticsTab === 'overview'" class="space-y-6">
            <!-- Product Overview Section -->
            <Card class="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
              <CardHeader>
                <CardTitle class="flex items-center gap-2 text-blue-900">
                  <Shield class="h-6 w-6" />
                  TPRM Risk Intelligence Platform
                </CardTitle>
                <CardDescription class="text-blue-700">
                  Comprehensive Third Party Risk Management solution providing real-time risk assessment, 
                  predictive analytics, and automated mitigation workflows across your entire vendor ecosystem.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div class="text-center p-4 bg-white rounded-lg border border-blue-100">
                    <div class="text-2xl font-bold text-blue-600">1,247</div>
                    <p class="text-sm text-gray-600">Active Vendors</p>
                  </div>
                  <div class="text-center p-4 bg-white rounded-lg border border-blue-100">
                    <div class="text-2xl font-bold text-green-600">892</div>
                    <p class="text-sm text-gray-600">Contracts Managed</p>
                  </div>
                  <div class="text-center p-4 bg-white rounded-lg border border-blue-100">
                    <div class="text-2xl font-bold text-purple-600">156</div>
                    <p class="text-sm text-gray-600">BCP/DRP Plans</p>
                  </div>
                  <div class="text-center p-4 bg-white rounded-lg border border-blue-100">
                    <div class="text-2xl font-bold text-orange-600">94.2%</div>
                    <p class="text-sm text-gray-600">Risk Coverage</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle class="flex items-center gap-2">
                    <PieChartIcon class="h-5 w-5 text-blue-600" />
                    Risk Distribution by Category
                  </CardTitle>
                  <CardDescription>Current risk landscape across all modules</CardDescription>
                </CardHeader>
                <CardContent>
                  <div class="h-80">
                    <div v-if="riskDistributionData && riskDistributionData.length > 0">
                      <div class="h-80 flex items-center justify-center">
                        <Doughnut 
                          :data="riskDistributionChartData" 
                          :options="pieChartOptions"
                          class="max-w-sm"
                        />
                      </div>
                    </div>
                    <div v-else class="flex items-center justify-center h-full text-gray-500">
                      <div class="text-center">
                        <PieChartIcon class="h-12 w-12 mx-auto mb-2 text-gray-300" />
                        <p>Loading chart data...</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle class="flex items-center gap-2">
                    <BarChart3 class="h-5 w-5 text-green-600" />
                    Risk Score Distribution
                  </CardTitle>
                  <CardDescription>Risk score breakdown by priority level</CardDescription>
                </CardHeader>
                <CardContent>
                  <div class="h-80">
                    <div v-if="riskScoreData && riskScoreData.length > 0">
                      <div class="h-80 flex items-center justify-center">
                        <Bar 
                          :data="riskScoreChartData" 
                          :options="barChartOptions"
                          class="w-full"
                        />
                      </div>
                    </div>
                    <div v-else class="flex items-center justify-center h-full text-gray-500">
                      <div class="text-center">
                        <BarChart3 class="h-12 w-12 mx-auto mb-2 text-gray-300" />
                        <p>Loading chart data...</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- Risk Metrics Grid -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle class="text-lg">Risk Velocity</CardTitle>
                  <CardDescription>Rate of new risks identified</CardDescription>
                </CardHeader>
                <CardContent>
                  <div class="text-3xl font-bold text-blue-600 mb-2">+12.5%</div>
                  <p class="text-sm text-gray-600">vs last month</p>
                  <div class="flex items-center mt-2">
                    <TrendingUp class="h-4 w-4 text-green-500 mr-1" />
                    <span class="text-sm text-green-600">Improving trend</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle class="text-lg">Mitigation Rate</CardTitle>
                  <CardDescription>Average time to mitigate risks</CardDescription>
                </CardHeader>
                <CardContent>
                  <div class="text-3xl font-bold text-green-600 mb-2">7.2 days</div>
                  <p class="text-sm text-gray-600">average resolution time</p>
                  <div class="flex items-center mt-2">
                    <TrendingUp class="h-4 w-4 text-green-500 mr-1" />
                    <span class="text-sm text-green-600">-2.1 days vs last month</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle class="text-lg">Risk Coverage</CardTitle>
                  <CardDescription>Percentage of assets assessed</CardDescription>
                </CardHeader>
                <CardContent>
                  <div class="text-3xl font-bold text-blue-600 mb-2">94.2%</div>
                  <p class="text-sm text-gray-600">of critical assets covered</p>
                  <div class="flex items-center mt-2">
                    <Target class="h-4 w-4 text-blue-500 mr-1" />
                    <span class="text-sm text-blue-600">Above target (90%)</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- Key Features Section -->
            <Card>
              <CardHeader>
                <CardTitle>Platform Key Features</CardTitle>
                <CardDescription>Advanced risk management capabilities powered by AI and machine learning</CardDescription>
              </CardHeader>
              <CardContent>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div class="flex items-start gap-3">
                    <div class="p-2 bg-blue-100 rounded-lg">
                      <Zap class="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 class="font-semibold text-gray-900">AI-Powered Risk Analysis</h4>
                      <p class="text-sm text-gray-600">LLaMA-based risk assessment with 95% accuracy</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-3">
                    <div class="p-2 bg-green-100 rounded-lg">
                      <Activity class="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <h4 class="font-semibold text-gray-900">Real-time Monitoring</h4>
                      <p class="text-sm text-gray-600">Continuous risk monitoring and alerting</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-3">
                    <div class="p-2 bg-purple-100 rounded-lg">
                      <Shield class="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <h4 class="font-semibold text-gray-900">Automated Workflows</h4>
                      <p class="text-sm text-gray-600">Streamlined approval and mitigation processes</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-3">
                    <div class="p-2 bg-orange-100 rounded-lg">
                      <BarChart3 class="h-5 w-5 text-orange-600" />
                    </div>
                    <div>
                      <h4 class="font-semibold text-gray-900">Predictive Analytics</h4>
                      <p class="text-sm text-gray-600">Forecast risk trends and potential issues</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-3">
                    <div class="p-2 bg-red-100 rounded-lg">
                      <Users class="h-5 w-5 text-red-600" />
                    </div>
                    <div>
                      <h4 class="font-semibold text-gray-900">Vendor Lifecycle</h4>
                      <p class="text-sm text-gray-600">Complete vendor management from onboarding to offboarding</p>
                    </div>
                  </div>
                  <div class="flex items-start gap-3">
                    <div class="p-2 bg-yellow-100 rounded-lg">
                      <FileText class="h-5 w-5 text-yellow-600" />
                    </div>
                    <div>
                      <h4 class="font-semibold text-gray-900">Compliance Tracking</h4>
                      <p class="text-sm text-gray-600">Automated compliance monitoring and reporting</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>


          <!-- Heatmap Tab -->
          <TabsContent value="heatmap" :active="activeAnalyticsTab === 'heatmap'" class="space-y-6">
            <!-- Heatmap Overview -->
            <Card class="bg-gradient-to-r from-orange-50 to-red-50 border-orange-200">
              <CardHeader>
                <CardTitle class="flex items-center gap-2 text-orange-900">
                  <Activity class="h-6 w-6" />
                  Risk Heatmap Analysis
                </CardTitle>
                <CardDescription class="text-orange-700">
                  Visual risk concentration analysis across departments, regions, and impact-likelihood matrix for strategic decision making.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div class="text-center p-4 bg-white rounded-lg border border-orange-100">
                    <div class="text-2xl font-bold text-red-600">8.2</div>
                    <p class="text-sm text-gray-600">Highest Dept Risk</p>
                  </div>
                  <div class="text-center p-4 bg-white rounded-lg border border-orange-100">
                    <div class="text-2xl font-bold text-orange-600">45</div>
                    <p class="text-sm text-gray-600">High Impact Risks</p>
                  </div>
                  <div class="text-center p-4 bg-white rounded-lg border border-orange-100">
                    <div class="text-2xl font-bold text-yellow-600">3.9</div>
                    <p class="text-sm text-gray-600">Lowest Region Risk</p>
                  </div>
                  <div class="text-center p-4 bg-white rounded-lg border border-orange-100">
                    <div class="text-2xl font-bold text-green-600">38</div>
                    <p class="text-sm text-gray-600">Low Likelihood Risks</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle class="flex items-center gap-2">
                    <Activity class="h-5 w-5 text-blue-600" />
                    Risk Heatmap by Department
                  </CardTitle>
                  <CardDescription>Risk concentration across organizational units</CardDescription>
                </CardHeader>
                <CardContent>
                  <div class="space-y-4">
                    <div v-for="dept in departmentRiskData" :key="dept.name" class="flex items-center justify-between p-4 border rounded-lg">
                      <div class="flex items-center gap-4">
                        <div 
                          class="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg"
                          :style="{ backgroundColor: dept.color }"
                        >
                          {{ dept.score }}
                        </div>
                        <div>
                          <h3 class="font-semibold text-gray-900">{{ dept.name }}</h3>
                          <p class="text-sm text-gray-600">{{ dept.riskCount }} risks identified</p>
                        </div>
                      </div>
                      <div class="text-right">
                        <Badge :variant="dept.badgeVariant" class="mb-2">
                          {{ dept.level }}
                        </Badge>
                        <div class="text-sm text-gray-600">
                          {{ ((dept.score / 10) * 100).toFixed(0) }}% risk level
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle class="flex items-center gap-2">
                    <Map class="h-5 w-5 text-green-600" />
                    Geographic Risk Distribution
                  </CardTitle>
                  <CardDescription>Risk levels by geographic regions</CardDescription>
                </CardHeader>
                <CardContent>
                  <div class="space-y-4">
                    <div v-for="region in geographicRiskData" :key="region.name" class="flex items-center justify-between p-4 border rounded-lg">
                      <div class="flex items-center gap-4">
                        <div :class="`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${region.colorClass}`">
                          {{ region.score }}
                        </div>
                        <div>
                          <h4 class="font-semibold">{{ region.name }}</h4>
                          <p class="text-sm text-gray-600">{{ region.riskCount }} risks</p>
                        </div>
                      </div>
                      <div class="text-right">
                        <div class="text-lg font-bold" :class="region.scoreColor">{{ region.score }}/10</div>
                        <Badge :variant="region.badgeVariant">{{ region.level }}</Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- Risk Matrix Heatmap -->
            <Card>
              <CardHeader>
                <CardTitle>Risk Impact vs Likelihood Matrix</CardTitle>
                <CardDescription>Visual representation of risk positioning - Hover over cells for details</CardDescription>
              </CardHeader>
              <CardContent>
                <div class="space-y-4">
                  <!-- Matrix Labels -->
                  <div class="flex justify-between items-end mb-2">
                    <div class="w-20"></div>
                    <div class="flex-1 text-center">
                      <div class="text-sm font-semibold text-gray-700 mb-2">Likelihood</div>
                      <div class="flex justify-between text-xs text-gray-600">
                        <span>Low</span>
                        <span>Medium</span>
                        <span>High</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Matrix Grid -->
                  <div class="grid grid-cols-6 gap-2 max-w-2xl mx-auto">
                    <!-- Y-axis label -->
                    <div class="flex flex-col justify-between h-32 text-xs text-gray-600">
                      <span class="text-right">High</span>
                      <span class="text-right">Medium</span>
                      <span class="text-right">Low</span>
                    </div>
                    
                    <!-- Matrix cells -->
                    <div class="grid grid-cols-5 gap-1">
                      <div v-for="cell in riskMatrix" :key="`${cell.impact}-${cell.likelihood}`" 
                           :class="`h-8 rounded flex items-center justify-center text-xs font-semibold text-white ${cell.color} hover:scale-105 transition-transform cursor-pointer`"
                           :title="`Impact: ${cell.impact}/5, Likelihood: ${cell.likelihood}/5 - ${cell.risks} risks`">
                        {{ cell.risks }}
                      </div>
                    </div>
                  </div>
                  
                  <!-- Legend -->
                  <div class="flex justify-center gap-4 mt-4 text-xs">
                    <div class="flex items-center gap-1">
                      <div class="w-3 h-3 bg-green-400 rounded"></div>
                      <span>Low Risk</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <div class="w-3 h-3 bg-yellow-400 rounded"></div>
                      <span>Medium Risk</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <div class="w-3 h-3 bg-orange-400 rounded"></div>
                      <span>High Risk</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <div class="w-3 h-3 bg-red-500 rounded"></div>
                      <span>Critical Risk</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <!-- Additional Heatmap Visualizations -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle class="flex items-center gap-2">
                    <BarChart3 class="h-5 w-5 text-purple-600" />
                    Risk Concentration by Business Unit
                  </CardTitle>
                  <CardDescription>Risk density across different business units</CardDescription>
                </CardHeader>
                <CardContent>
                  <div v-if="businessUnitRiskData && businessUnitRiskData.length > 0" class="h-80 w-full">
                    <Bar 
                      :data="businessUnitRiskChartData" 
                      :options="horizontalBarChartOptions"
                    />
                  </div>
                  <div v-else class="flex items-center justify-center h-80 text-gray-500">
                    <div class="text-center">
                      <BarChart3 class="h-12 w-12 mx-auto mb-2 text-gray-300" />
                      <p>Loading chart data...</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle class="flex items-center gap-2">
                    <PieChartIcon class="h-5 w-5 text-indigo-600" />
                    Risk Distribution by Severity
                  </CardTitle>
                  <CardDescription>Breakdown of risks by severity levels</CardDescription>
                </CardHeader>
                <CardContent>
                  <div class="h-80">
                    <div v-if="severityDistributionData && severityDistributionData.length > 0">
                      <div class="h-80 flex items-center justify-center">
                        <Doughnut 
                          :data="severityDistributionChartData" 
                          :options="pieChartOptions"
                          class="max-w-sm"
                        />
                      </div>
                    </div>
                    <div v-else class="flex items-center justify-center h-full text-gray-500">
                      <div class="text-center">
                        <PieChartIcon class="h-12 w-12 mx-auto mb-2 text-gray-300" />
                        <p>Loading chart data...</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- Heatmap Insights -->
            <Card>
              <CardHeader>
                <CardTitle>Heatmap Insights & Recommendations</CardTitle>
                <CardDescription>Strategic insights based on risk concentration analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div class="space-y-4">
                    <h4 class="font-semibold text-gray-900">Risk Concentration Analysis</h4>
                    <ul class="space-y-3 text-sm text-gray-600">
                      <li class="flex items-start gap-2">
                        <div class="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span><strong>IT Operations</strong> shows highest risk concentration (8.2/10) - requires immediate attention</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <div class="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span><strong>Finance Department</strong> has medium risk levels (6.1/10) - monitor closely</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <div class="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span><strong>HR and Legal</strong> departments show low risk levels - maintain current processes</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <div class="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span><strong>North America</strong> region has highest geographic risk concentration</span>
                      </li>
                    </ul>
                  </div>
                  <div class="space-y-4">
                    <h4 class="font-semibold text-gray-900">Recommended Actions</h4>
                    <div class="space-y-3">
                      <div class="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <h5 class="font-medium text-red-800">Immediate Actions</h5>
                        <p class="text-sm text-red-700">Focus risk mitigation efforts on IT Operations and North America region</p>
                      </div>
                      <div class="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <h5 class="font-medium text-yellow-800">Short-term Actions</h5>
                        <p class="text-sm text-yellow-700">Implement additional monitoring for Finance department risks</p>
                      </div>
                      <div class="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <h5 class="font-medium text-green-800">Long-term Strategy</h5>
                        <p class="text-sm text-green-700">Replicate successful risk management practices from HR/Legal to other departments</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

        </Tabs>
      </div>

      <!-- Module Risk Overview -->
      <div class="mb-12">
        <h2 class="text-3xl font-bold text-gray-900 mb-8">Module Risk Overview</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="navigateToVendorRisk">
            <CardHeader>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="p-2 bg-red-100 rounded-lg">
                    <Building2 class="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <CardTitle class="text-lg">Vendor Risk</CardTitle>
                    <CardDescription>Third-party vendor assessments</CardDescription>
                  </div>
                </div>
                <Badge variant="destructive">High Risk</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Critical Risks:</span>
                  <span class="font-semibold text-red-600">12</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Active Vendors:</span>
                  <span class="font-semibold">1,247</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Avg Risk Score:</span>
                  <span class="font-semibold text-orange-600">6.8/10</span>
                </div>
              </div>
              <div class="mt-4">
                <div class="flex items-center text-sm text-gray-600">
                  <AlertTriangle class="h-4 w-4 mr-1 text-red-500" />
                  <span>8 vendors require immediate attention</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="navigateToContractRisk">
            <CardHeader>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="p-2 bg-orange-100 rounded-lg">
                    <FileText class="h-6 w-6 text-orange-600" />
                  </div>
                  <div>
                    <CardTitle class="text-lg">Contract Risk</CardTitle>
                    <CardDescription>Contract analysis & compliance</CardDescription>
                  </div>
                </div>
                <Badge variant="secondary" class="bg-orange-100 text-orange-800">Medium Risk</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Critical Risks:</span>
                  <span class="font-semibold text-red-600">7</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Active Contracts:</span>
                  <span class="font-semibold">892</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Avg Risk Score:</span>
                  <span class="font-semibold text-yellow-600">5.2/10</span>
                </div>
              </div>
              <div class="mt-4">
                <div class="flex items-center text-sm text-gray-600">
                  <Clock class="h-4 w-4 mr-1 text-orange-500" />
                  <span>15 contracts expiring soon</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="navigateToBCPRisk">
            <CardHeader>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <div class="p-2 bg-purple-100 rounded-lg">
                    <Shield class="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <CardTitle class="text-lg">BCP/DRP Risk</CardTitle>
                    <CardDescription>Business continuity planning</CardDescription>
                  </div>
                </div>
                <Badge variant="outline" class="text-green-700 border-green-300">Low Risk</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Critical Risks:</span>
                  <span class="font-semibold text-red-600">4</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Active Plans:</span>
                  <span class="font-semibold">156</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-sm text-gray-600">Avg Risk Score:</span>
                  <span class="font-semibold text-green-600">3.1/10</span>
                </div>
              </div>
              <div class="mt-4">
                <div class="flex items-center text-sm text-gray-600">
                  <CheckCircle class="h-4 w-4 mr-1 text-green-500" />
                  <span>Most plans are up to date</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>


      <!-- Recent Risk Alerts -->
      <div class="mb-12">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Bell class="h-5 w-5 text-red-600" />
              Recent Risk Alerts
            </CardTitle>
            <CardDescription>Latest risk notifications requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div v-for="alert in recentAlerts" :key="alert.id" class="flex items-start gap-4 p-4 border rounded-lg">
                <div :class="`p-2 rounded-full ${alert.iconBg}`">
                  <component :is="alert.icon" :class="`h-5 w-5 ${alert.iconColor}`" />
                </div>
                <div class="flex-1">
                  <div class="flex items-center justify-between">
                    <h4 class="font-semibold text-gray-900">{{ alert.title }}</h4>
                    <Badge :variant="alert.badgeVariant">{{ alert.priority }}</Badge>
                  </div>
                  <p class="text-sm text-gray-600 mt-1">{{ alert.description }}</p>
                  <p class="text-xs text-gray-500 mt-2">{{ alert.timestamp }}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Risk Mitigation Progress -->
      <div class="mb-12">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Target class="h-5 w-5 text-green-600" />
              Risk Mitigation Progress
            </CardTitle>
            <CardDescription>Current status of risk mitigation initiatives</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="text-center">
                <div class="text-3xl font-bold text-green-600 mb-2">68%</div>
                <p class="text-sm text-gray-600">Mitigation Complete</p>
                <div class="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div class="bg-green-600 h-2 rounded-full" style="width: 68%"></div>
                </div>
              </div>
              <div class="text-center">
                <div class="text-3xl font-bold text-blue-600 mb-2">24%</div>
                <p class="text-sm text-gray-600">In Progress</p>
                <div class="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div class="bg-blue-600 h-2 rounded-full" style="width: 24%"></div>
                </div>
              </div>
              <div class="text-center">
                <div class="text-3xl font-bold text-red-600 mb-2">8%</div>
                <p class="text-sm text-gray-600">Pending</p>
                <div class="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div class="bg-red-600 h-2 rounded-full" style="width: 8%"></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Footer CTA -->
    <div class="bg-gray-900 text-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div class="text-center">
          <h2 class="text-3xl font-bold mb-4">Ready to Enhance Your Risk Management?</h2>
          <p class="text-xl text-gray-300 mb-8">
            Get started with comprehensive risk assessment and monitoring
          </p>
          <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" class="bg-blue-600 hover:bg-blue-700">
              <Shield class="h-5 w-5 mr-2" />
              Start Risk Assessment
            </Button>
            <Button size="lg" variant="outline" class="border-white text-white hover:bg-white hover:text-gray-900">
              <BookOpen class="h-5 w-5 mr-2" />
              Learn More
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Filler } from 'chart.js'
import { Doughnut, Bar, Line } from 'vue-chartjs'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Filler)
import {
  Shield,
  BarChart3,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Building2,
  Target,
  PieChart as PieChartIcon,
  Activity,
  FileText,
  Clock,
  CheckCircle,
  Bell,
  BookOpen,
  Download,
  RefreshCw,
  Map,
  Users,
  Zap
} from 'lucide-vue-next'

const router = useRouter()
const store = useStore()
const activeAnalyticsTab = ref('overview')

// Static data for charts
const riskDistributionData = ref([
  { name: 'Vendor Risk', value: 45, color: '#ef4444' },
  { name: 'Contract Risk', value: 28, color: '#f97316' },
  { name: 'BCP/DRP Risk', value: 15, color: '#8b5cf6' },
  { name: 'SLA Risk', value: 12, color: '#06b6d4' }
])


// Additional analytics data
const riskScoreData = ref([
  { scoreRange: '0-2', count: 15 },
  { scoreRange: '3-4', count: 28 },
  { scoreRange: '5-6', count: 45 },
  { scoreRange: '7-8', count: 32 },
  { scoreRange: '9-10', count: 18 }
])


const geographicRiskData = ref([
  { name: 'North America', score: 7.2, riskCount: 45, level: 'High', colorClass: 'bg-red-500', scoreColor: 'text-red-600', badgeVariant: 'destructive' },
  { name: 'Europe', score: 5.8, riskCount: 32, level: 'Medium', colorClass: 'bg-orange-500', scoreColor: 'text-orange-600', badgeVariant: 'secondary' },
  { name: 'Asia Pacific', score: 4.1, riskCount: 28, level: 'Low', colorClass: 'bg-yellow-500', scoreColor: 'text-yellow-600', badgeVariant: 'outline' },
  { name: 'Latin America', score: 3.9, riskCount: 15, level: 'Low', colorClass: 'bg-green-500', scoreColor: 'text-green-600', badgeVariant: 'outline' }
])

const riskMatrix = ref([
  // Low Impact (1-2)
  { impact: 1, likelihood: 1, risks: 5, color: 'bg-green-400' },
  { impact: 1, likelihood: 2, risks: 8, color: 'bg-green-300' },
  { impact: 2, likelihood: 1, risks: 6, color: 'bg-green-300' },
  { impact: 2, likelihood: 2, risks: 12, color: 'bg-yellow-300' },
  // Medium Impact (3-4)
  { impact: 3, likelihood: 1, risks: 7, color: 'bg-green-300' },
  { impact: 3, likelihood: 2, risks: 15, color: 'bg-yellow-300' },
  { impact: 3, likelihood: 3, risks: 18, color: 'bg-yellow-400' },
  { impact: 4, likelihood: 1, risks: 9, color: 'bg-yellow-300' },
  { impact: 4, likelihood: 2, risks: 22, color: 'bg-yellow-400' },
  { impact: 4, likelihood: 3, risks: 25, color: 'bg-orange-400' },
  // High Impact (5)
  { impact: 5, likelihood: 1, risks: 11, color: 'bg-yellow-400' },
  { impact: 5, likelihood: 2, risks: 28, color: 'bg-orange-400' },
  { impact: 5, likelihood: 3, risks: 35, color: 'bg-orange-500' },
  { impact: 5, likelihood: 4, risks: 42, color: 'bg-red-400' },
  { impact: 5, likelihood: 5, risks: 38, color: 'bg-red-500' }
])


const businessUnitRiskData = ref([
  { unit: 'Sales', riskCount: 32 },
  { unit: 'Marketing', riskCount: 18 },
  { unit: 'Operations', riskCount: 45 },
  { unit: 'Finance', riskCount: 28 },
  { unit: 'IT', riskCount: 52 },
  { unit: 'HR', riskCount: 12 }
])

const severityDistributionData = ref([
  { name: 'Critical', value: 23, color: '#ef4444' },
  { name: 'High', value: 47, color: '#f97316' },
  { name: 'Medium', value: 89, color: '#eab308' },
  { name: 'Low', value: 135, color: '#22c55e' }
])

const departmentRiskData = ref([
  { name: 'IT Operations', score: 8.2, riskCount: 23, color: '#ef4444', level: 'High', badgeVariant: 'destructive' },
  { name: 'Finance', score: 6.1, riskCount: 18, color: '#f97316', level: 'Medium', badgeVariant: 'secondary' },
  { name: 'HR', score: 3.4, riskCount: 8, color: '#eab308', level: 'Low', badgeVariant: 'outline' },
  { name: 'Legal', score: 4.7, riskCount: 12, color: '#22c55e', level: 'Low', badgeVariant: 'outline' }
])

const recentAlerts = ref([
  {
    id: 1,
    title: 'Critical Vendor Risk Detected',
    description: 'TechCorp Solutions shows significant financial instability indicators',
    priority: 'Critical',
    timestamp: '2 hours ago',
    icon: AlertTriangle,
    iconColor: 'text-red-600',
    iconBg: 'bg-red-100',
    badgeVariant: 'destructive'
  },
  {
    id: 2,
    title: 'Contract Expiration Alert',
    description: '15 contracts expiring within 30 days require immediate attention',
    priority: 'High',
    timestamp: '4 hours ago',
    icon: Clock,
    iconColor: 'text-orange-600',
    iconBg: 'bg-orange-100',
    badgeVariant: 'secondary'
  },
  {
    id: 3,
    title: 'BCP Plan Update Required',
    description: 'Disaster recovery plan for Data Center A needs annual review',
    priority: 'Medium',
    timestamp: '1 day ago',
    icon: Shield,
    iconColor: 'text-blue-600',
    iconBg: 'bg-blue-100',
    badgeVariant: 'outline'
  },
  {
    id: 4,
    title: 'SLA Performance Degradation',
    description: 'Service level agreement with CloudProvider Inc. showing declining metrics',
    priority: 'Medium',
    timestamp: '2 days ago',
    icon: TrendingUp,
    iconColor: 'text-yellow-600',
    iconBg: 'bg-yellow-100',
    badgeVariant: 'outline'
  }
])

// Chart.js data configurations
const riskDistributionChartData = computed(() => ({
  labels: riskDistributionData.value.map(item => item.name),
  datasets: [{
    data: riskDistributionData.value.map(item => item.value),
    backgroundColor: riskDistributionData.value.map(item => item.color),
    borderWidth: 2,
    borderColor: '#ffffff'
  }]
}))

const riskScoreChartData = computed(() => ({
  labels: riskScoreData.value.map(item => item.scoreRange),
  datasets: [{
    label: 'Count',
    data: riskScoreData.value.map(item => item.count),
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
    borderWidth: 1
  }]
}))

const businessUnitRiskChartData = computed(() => ({
  labels: businessUnitRiskData.value.map(item => item.unit),
  datasets: [{
    label: 'Risk Count',
    data: businessUnitRiskData.value.map(item => item.riskCount),
    backgroundColor: '#8b5cf6',
    borderColor: '#8b5cf6',
    borderWidth: 1
  }]
}))

const severityDistributionChartData = computed(() => ({
  labels: severityDistributionData.value.map(item => item.name),
  datasets: [{
    data: severityDistributionData.value.map(item => item.value),
    backgroundColor: severityDistributionData.value.map(item => item.color),
    borderWidth: 2,
    borderColor: '#ffffff'
  }]
}))

// Chart.js options
const pieChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
    },
    tooltip: {
      callbacks: {
        label: function(context) {
          const label = context.label || '';
          const value = context.parsed;
          const total = context.dataset.data.reduce((a, b) => a + b, 0);
          const percentage = ((value / total) * 100).toFixed(1);
          return `${label}: ${value} (${percentage}%)`;
        }
      }
    }
  }
}))

const barChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true
    }
  }
}))

const horizontalBarChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'y',
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    x: {
      beginAtZero: true
    }
  }
}))

const lineChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
    }
  },
  scales: {
    y: {
      beginAtZero: true
    }
  }
}))

const areaChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true
    }
  }
}))

// Navigation functions
const navigateToVendorRisk = () => {
  router.push('/vendor-risk-scoring')
}

const navigateToContractRisk = () => {
  router.push('/contractdashboard')
}

const navigateToBCPRisk = () => {
  router.push('/bcp/general-dashboard')
}


onMounted(() => {
  // Any initialization logic can go here
  console.log('Home page mounted with risk data')
})

// Watch for tab changes
watch(activeAnalyticsTab, (newTab) => {
  console.log('Active tab changed to:', newTab)
})
</script>

<style scoped>
/* Custom styles for the home page */
.gradient-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.phase-card {
  transition: transform 0.2s ease-in-out;
}

.phase-card:hover {
  transform: translateY(-2px);
}

/* Ensure consistent tab styling */
:deep(.tabs-list) {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0;
  border-radius: 0.5rem;
  background-color: hsl(var(--muted));
  padding: 0.25rem;
}

:deep(.tabs-trigger) {
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
  border-radius: 0.375rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease-in-out;
  background-color: transparent;
  color: hsl(var(--muted-foreground));
  border: none;
  cursor: pointer;
  width: 100%;
  min-height: 2.5rem;
}

:deep(.tabs-trigger:hover) {
  background-color: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
}

:deep(.tabs-trigger[data-active="true"]) {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
}
</style>
