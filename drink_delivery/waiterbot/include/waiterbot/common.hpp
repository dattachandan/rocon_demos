/*
 * common.hpp
 *
 *  Created on: Apr 11, 2013
 *      Author: jorge
 */

#ifndef COMMON_HPP_
#define COMMON_HPP_


#include <tf/tf.h>

#include <geometry_msgs/Pose.h>
#include <geometry_msgs/PoseStamped.h>


namespace waiterbot
{

static const uint32_t AR_MARKERS_COUNT = 18;


namespace tk // toolkit
{

// Template functions
template <typename T> T mean(std::vector<T> v)
{
  T acc = 0;
  for (unsigned int i = 0; i < v.size(); i++)
    acc += v[i];
  return acc/v.size();
};

template <typename T> T variance(std::vector<T> v)
{
  T acc = 0;
  T avg = tk::mean(v);
  for (unsigned int i = 0; i < v.size(); i++)
    acc += std::pow(v[i] - avg, 2);
  return acc/(v.size() - 1);
};

template <typename T> T std_dev(std::vector<T> v)
{
  return std::sqrt(variance(v));
}

// Other functions

double pitch(geometry_msgs::Pose pose);
double pitch(geometry_msgs::PoseStamped pose);

double distance(geometry_msgs::Point a, geometry_msgs::Point b = geometry_msgs::Point());
double distance(geometry_msgs::Pose a, geometry_msgs::Pose b = geometry_msgs::Pose());

void tf2pose(const tf::Transform& tf, geometry_msgs::Pose& pose);
void tf2pose(const tf::StampedTransform& tf, geometry_msgs::PoseStamped& pose);

void pose2tf(const geometry_msgs::Pose& pose, tf::Transform& tf);
void pose2tf(const geometry_msgs::PoseStamped& pose, tf::StampedTransform& tf);

const char* pose2str(const geometry_msgs::Pose& pose);
const char* pose2str(const geometry_msgs::PoseStamped& pose);

void halfRingPoses(double radius, double height, int poses);

} /* namespace toolkit */
} /* namespace waiterbot */

#endif /* COMMON_HPP_ */