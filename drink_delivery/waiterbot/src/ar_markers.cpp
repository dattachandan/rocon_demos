/*
 * ar_markers.cpp
 *
 *  Created on: Apr 6, 2013
 *      Author: jorge
 */

#include "waiterbot/common.hpp"
#include "waiterbot/ar_markers.hpp"

namespace waiterbot
{

ARMarkers::ARMarkers()
{
  // Invalid id until we localize it globally
  docking_marker_.id = std::numeric_limits<uint32_t>::max();

/*
//TODO kk  quitar cuando lea globals/docking OK
  global_markers_.markers.push_back(ar_track_alvar::AlvarMarker());  // TODO do from semantic map!!!!!!!!!!!!!!
  global_markers_.markers[0].id = 0;
  global_markers_.markers[0].pose.header.frame_id = "map";
  global_markers_.markers[0].pose.pose.position.x = -0.2;
  global_markers_.markers[0].pose.pose.position.y = 1.6;
  global_markers_.markers[0].pose.pose.position.z = 0.3;
  global_markers_.markers[0].pose.pose.orientation = tf::createQuaternionMsgFromRollPitchYaw(M_PI/2.0, 0.0, M_PI/2.0);

  global_markers_.markers.push_back(ar_track_alvar::AlvarMarker());  // TODO do from semantic map!!!!!!!!!!!!!!
  global_markers_.markers[1].id = 1;
  global_markers_.markers[1].pose.header.frame_id = "map";
  global_markers_.markers[1].pose.pose.position.x = +0.2;
  global_markers_.markers[1].pose.pose.position.y = -1.6;
  global_markers_.markers[1].pose.pose.position.z = 0.3;
  global_markers_.markers[1].pose.pose.orientation = tf::createQuaternionMsgFromRollPitchYaw(M_PI/2.0, 0.0, -M_PI/2.0);

  docking_marker_.id = 4;
  docking_marker_.pose.header.frame_id = "map";
  docking_marker_.pose.pose.position.x = -0.1;
  docking_marker_.pose.pose.position.y = -1.9;
  docking_marker_.pose.pose.position.z = 0.1;
  docking_marker_.pose.pose.orientation = tf::createQuaternionMsgFromRollPitchYaw(M_PI/2.0, 0.0, M_PI);

  ROS_DEBUG("%.2f %.2f  %.2f  %.2f", docking_marker_.pose.pose.orientation.x, docking_marker_.pose.pose.orientation.y, docking_marker_.pose.pose.orientation.z, docking_marker_.pose.pose.orientation.w);
*/
}

ARMarkers::~ARMarkers()
{
}

bool ARMarkers::init()
{
  ros::NodeHandle nh, pnh("~");

  // Parameters
  pnh.param("tf_broadcast_freq", tf_brc_freq_, 0.0);  // disabled by default
  pnh.param("global_frame", global_frame_, std::string("map"));
  pnh.param("odom_frame",   odom_frame_,   std::string("odom"));
  pnh.param("base_frame",   base_frame_,   std::string("base_footprint"));

  tracked_markers_sub_ = nh.subscribe("ar_track_alvar/ar_pose_marker", 1, &ARMarkers::arPoseMarkersCB, this);
  global_markers_sub_  = nh.subscribe("semantic_map/marker_pose_list", 1, &ARMarkers::globalMarkersCB, this);

  // There are 18 different markers
  times_spotted_.resize(AR_MARKERS_COUNT, 0);

  if (tf_brc_freq_ > 0.0)
  {
    boost::thread(&ARMarkers::broadcastMarkersTF, this);
  }

  // Disable tracking until needed
  disableTracker();

  return true;
}

void ARMarkers::broadcastMarkersTF()
{
  ros::Rate rate(tf_brc_freq_);

  while (ros::ok())
  {
    char child_frame[32];
    tf::StampedTransform tf;
    tf.stamp_ = ros::Time::now();

    for (unsigned int i = 0; i <global_markers_.markers.size(); i++)
    {
      sprintf(child_frame, "global_marker_%d", global_markers_.markers[i].id);
      tk::pose2tf(global_markers_.markers[i].pose, tf);
      tf.child_frame_id_ = child_frame;
      tf.stamp_ = ros::Time::now();
      tf_brcaster_.sendTransform(tf);
    }

//TODO esto sobra
    if (docking_marker_.id != std::numeric_limits<uint32_t>::max())
    {
      sprintf(child_frame, "docking_base_%d", docking_marker_.id);
      tk::pose2tf(docking_marker_.pose, tf);
      tf.child_frame_id_ = child_frame;
      tf.stamp_ = ros::Time::now();
      tf_brcaster_.sendTransform(tf);
    }

    rate.sleep();
    //ros::Duration(1.0/tf_brc_freq_).sleep();
  }
}

void ARMarkers::globalMarkersCB(const ar_track_alvar::AlvarMarkers::Ptr& msg)
{
  if ((global_markers_.markers.size() == 0) && (msg->markers.size() > 0))  // first message; ignore the rest
  {
    global_markers_ = *msg;
    ROS_INFO("%u global marker pose(s) received", global_markers_.markers.size());
    for (unsigned int i = 0; i < global_markers_.markers.size(); i++)
    {

//TODO cheat for debuging;  remove
      if (global_markers_.markers[i].id >= 4)
      {
        ROS_DEBUG("Docking marker %d: %s", global_markers_.markers[i].id, tk::pose2str(global_markers_.markers[i].pose.pose));
        docking_marker_ = global_markers_.markers[i];
        global_markers_.markers.pop_back();
      }
      else


      ROS_DEBUG("Marker %d: %s", global_markers_.markers[i].id, tk::pose2str(global_markers_.markers[i].pose.pose));
    }
  }
}

void ARMarkers::arPoseMarkersCB(const ar_track_alvar::AlvarMarkers::Ptr& msg)
{
  // TODO MAke pointer!!!!  to avoid copying    but take care of multi-threading
  // more TODO:  inc confidence is very shitty as quality measure ->  we need a filter!!!  >>>   and also incorporate on covariance!!!!

  for (unsigned int i = 0; i < msg->markers.size(); i++)
  {
    // Sometimes markers are spotted "inverted" (pointing to -y); as we assume that all the markers are
    // aligned with y pointing up, x pointing right and z pointing to the observer, that's a recognition
    // error. Instead of fixing, we discard the whole message, so tf with this timestamp are not used
    tf::Quaternion q;
    double roll, pitch, yaw;
    tf::quaternionMsgToTF(msg->markers[i].pose.pose.orientation, q);
    tf::Matrix3x3(q).getRPY(roll, pitch, yaw);
//    ROS_DEBUG("RPY = (%lf, %lf, %lf)    %.2f  %.2f  %.2f  %.2f", roll, pitch, yaw,   msg->markers[i].pose.pose.orientation.x, msg->markers[i].pose.pose.orientation.y, msg->markers[i].pose.pose.orientation.z, msg->markers[i].pose.pose.orientation.w);
    if (tk::pitch(msg->markers[i].pose.pose) > 1.0)
    {
      ROS_WARN("Discarding down-pointing AR marker (%d)     (%f, %f, %f)   %.2f  %.2f  %.2f  %.2f", msg->markers[i].id,      roll, pitch, yaw,    msg->markers[i].pose.pose.orientation.x, msg->markers[i].pose.pose.orientation.y, msg->markers[i].pose.pose.orientation.z, msg->markers[i].pose.pose.orientation.w);
      return;
    }
  }

  for (unsigned int i = 0; i < msg->markers.size(); i++)
  {
    if (msg->markers[i].id >= times_spotted_.size())
    {
      // A recognition error from Alvar markers tracker
      ROS_WARN("Discarding AR marker with unrecognized id (%d)", msg->markers[i].id);
      continue;
    }

    times_spotted_[msg->markers[i].id] += 2;

    if ((msg->markers[i].id == docking_marker_.id) &&
        (times_spotted_[msg->markers[i].id] > 4))  // publish only with 3 or more spots
    {
      // This is the docking base marker! call the registered callbacks
      boost::shared_ptr<geometry_msgs::PoseStamped> ps(new geometry_msgs::PoseStamped());
      *ps = msg->markers[i].pose;
      base_spotted_cb_(ps, msg->markers[i].id);
    }

    ar_track_alvar::AlvarMarker global_marker;
    if ((included(msg->markers[i].id, global_markers_, &global_marker) == true) &&
        (times_spotted_[msg->markers[i].id] > 4))  // publish only with 3 or more spots
    {
      // This is a global marker! infer the robot's global pose and call the registered callbacks
      boost::shared_ptr<geometry_msgs::PoseWithCovarianceStamped> pwcs(new geometry_msgs::PoseWithCovarianceStamped);

      char marker_frame[32];
      sprintf(marker_frame, "ar_marker_%d", msg->markers[i].id);

      try
      {
        tf::StampedTransform marker_gb; // marker on global reference system
        tk::pose2tf(global_marker.pose, marker_gb);

        // Get marker tf on global reference system; note that we look for the same timestamp that
        // the AlvarMarker message to avoid the inverted marker phenomenon; see above for details
        tf::StampedTransform robot_mk;
        tf_listener_.waitForTransform(marker_frame, base_frame_, msg->markers[i].header.stamp, ros::Duration(0.05));
        tf_listener_.lookupTransform(marker_frame, base_frame_, msg->markers[i].header.stamp, robot_mk);

        tf::Transform robot_gb = marker_gb*robot_mk;
        tk::tf2pose(robot_gb, pwcs->pose.pose);
      }
      catch (tf::TransformException& e)
      {
        ROS_ERROR("Cannot get tf %s -> %s: %s", global_frame_.c_str(), marker_frame, e.what());
        continue;
      }

      pwcs->header.stamp = msg->header.stamp;
      pwcs->header.frame_id = global_frame_;

      robot_pose_cb_(pwcs);
    }
  }
  spotted_markers_ = *msg;

//if (spotted_markers_.markers.size()> 0)   ROS_ERROR("MK  %d  %d   %f", spotted_markers_.markers[0].id, times_spotted_[spotted_markers_.markers[0].id], spotted_markers_.header.stamp.toSec());

  // Decay ALL markers; that's why spotted ones got a +2 on times spotted
  for (unsigned int i = 0; i < times_spotted_.size(); i++)
  {
    if (times_spotted_[i] > 0)
      times_spotted_[i]--;
  }
}

bool ARMarkers::spotted(double younger_than,
                        const ar_track_alvar::AlvarMarkers& including,
                        const ar_track_alvar::AlvarMarkers& excluding,
                              ar_track_alvar::AlvarMarkers& spotted)
{
  if (spotted_markers_.markers.size() == 0)
    return false;

  if ((ros::Time::now() - spotted_markers_.markers[0].header.stamp).toSec() >= younger_than)
  {
    return false;
  }

  spotted.header = spotted_markers_.header;
  spotted.markers.clear();
  for (unsigned int i = 0; i < spotted_markers_.markers.size(); i++)
  {
    if ((included(spotted_markers_.markers[i].id, including) == true) &&
        (excluded(spotted_markers_.markers[i].id, excluding) == true))
    {
      spotted.markers.push_back(spotted_markers_.markers[i]);
    }
  }

  return (spotted.markers.size() > 0);
}

bool ARMarkers::closest(const ar_track_alvar::AlvarMarkers& including,
                        const ar_track_alvar::AlvarMarkers& excluding,
                              ar_track_alvar::AlvarMarker& closest)
{
  double closest_dist = std::numeric_limits<double>::max();
  for (unsigned int i = 0; i < spotted_markers_.markers.size(); i++)
  {
    if ((included(spotted_markers_.markers[i].id, including) == true) &&
        (excluded(spotted_markers_.markers[i].id, excluding) == true))
    {
      double d = tk::distance(spotted_markers_.markers[i].pose.pose.position);
      if (d < closest_dist)
      {
        closest_dist = d;
        closest = spotted_markers_.markers[i];
      }
    }
  }

  return (closest_dist < std::numeric_limits<double>::max());
}

bool ARMarkers::spotted(double younger_than, int min_confidence, bool exclude_globals,
                        ar_track_alvar::AlvarMarkers& spotted)
{
  if (spotted_markers_.markers.size() == 0)
    return false;

  if ((ros::Time::now() - spotted_markers_.markers[0].header.stamp).toSec() >= younger_than)
  {
    // We must check the timestamp from an element in the markers list, as the one on message's header is always zero!
    // WARNING: parameter younger_than must be high enough, as ar_track_alvar publish at Kinect rate but only updates
    // timestamps about every 0.1 seconds (and now we can set it to run slower, as frequency is a dynamic parameter!)
    ROS_WARN("Spotted markers too old:   %f  >=  %f",   (ros::Time::now() - spotted_markers_.markers[0].header.stamp).toSec(), younger_than);
    return false;
  }

  spotted.header = spotted_markers_.header;
  spotted.markers.clear();
  for (unsigned int i = 0; i < spotted_markers_.markers.size(); i++)
  {
    if ((exclude_globals == true) && (included(spotted_markers_.markers[i].id, global_markers_) == true))
      continue;

    if (times_spotted_[spotted_markers_.markers[i].id] >= min_confidence)
    {
      spotted.markers.push_back(spotted_markers_.markers[i]);
    }
  }

  return (spotted.markers.size() > 0);
}

bool ARMarkers::closest(double younger_than, int min_confidence, bool exclude_globals,
                        ar_track_alvar::AlvarMarker& closest)
{
  ar_track_alvar::AlvarMarkers spotted_markers;
  if (spotted(younger_than, min_confidence, exclude_globals, spotted_markers) == false)
    return false;

  double closest_dist = std::numeric_limits<double>::max();
  for (unsigned int i = 0; i < spotted_markers.markers.size(); i++)
  {
    double d = tk::distance(spotted_markers.markers[i].pose.pose.position);
    if (d < closest_dist)
    {
      closest_dist = d;
      closest = spotted_markers.markers[i];
    }
  }

  return (closest_dist < std::numeric_limits<double>::max());
}

bool ARMarkers::spotDockMarker(uint32_t base_marker_id)
{
  for (unsigned int i = 0; i < spotted_markers_.markers.size(); i++)
  {
    if (spotted_markers_.markers[i].id == base_marker_id)
    {
      if (times_spotted_[spotted_markers_.markers[i].id] < 2)
      {
        ROS_WARN("Low confidence on spotted docking marker. Dangerous...", spotted_markers_.markers[i].confidence);
        // TODO   this can be catastrophic if we are very unlucky
      }

      docking_marker_ = spotted_markers_.markers[i];
      docking_marker_.header.frame_id = global_frame_;
      docking_marker_.pose.header.frame_id = global_frame_;

      char marker_frame[32];
      sprintf(marker_frame, "ar_marker_%d", base_marker_id);

      try
      {
        // Get marker tf on global reference system; note that we look for the same timestamp that
        // the AlvarMarker message to avoid the inverted marker phenomenon; see comments on method
        // ARMarkers::arPoseMarkerCB for more details
        tf::StampedTransform marker_gb;
        tf_listener_.waitForTransform(global_frame_, marker_frame,
                                      docking_marker_.pose.header.stamp, ros::Duration(0.05));
        tf_listener_.lookupTransform(global_frame_, marker_frame,
                                     docking_marker_.pose.header.stamp, marker_gb);

        tk::tf2pose(marker_gb, docking_marker_.pose.pose);

        global_markers_.markers.push_back(docking_marker_);
        ROS_DEBUG("Docking AR marker registered with global pose: %.2f, %.2f, %.2f",
                  docking_marker_.pose.pose.position.x, docking_marker_.pose.pose.position.y,
                  tf::getYaw(docking_marker_.pose.pose.orientation));
        return true;
      }
      catch (tf::TransformException& e)
      {
        ROS_ERROR("Cannot get tf %s -> %s: %s", global_frame_.c_str(), marker_frame, e.what());
        return false;
      }
    }
  }

  // Cannot spot docking marker
  return false;
}

bool ARMarkers::enableTracker()
{
  int status = system("rosrun dynamic_reconfigure dynparam set ar_track_alvar \"{ enabled: true }\"");

  if (status != 0)
  {
    ROS_ERROR("Enable AR markers tracker failed (%d/%d)", status, WEXITSTATUS(status));
    return false;
  }

  return true;
}

bool ARMarkers::disableTracker()
{
//  char system_cmd[256];
//  snprintf(system_cmd, 256,
//           "rosrun dynamic_reconfigure dynparam set ar_track_alvar \"{ enabled: true }\"");
  // TODO I think I can also call /ar_track_alvar/set_parameters... if the server is not up, system call blocks,
  // what is very shity; another option is create a generic tk::waitForServer and reuse for action servers
  int status = system("rosrun dynamic_reconfigure dynparam set ar_track_alvar \"{ enabled: false }\"");
  if (status != 0)
  {
    ROS_ERROR("Disable AR markers tracker failed (%d/%d)", status, WEXITSTATUS(status));
    return false;
  }

  return true;
}


} /* namespace waiterbot */